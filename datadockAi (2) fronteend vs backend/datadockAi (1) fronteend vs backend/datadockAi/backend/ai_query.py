"""
DataDock AI — Natural-Language-to-SQL & Query Explainer
Integrates Google Gemini (via google-genai SDK) with reliable offline fallback.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional

from sql_engine import validate_query_safety, SQLSecurityError

# Google Gen AI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def _heuristic_sql_fallback(prompt: str, schema: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """
    Deterministic rule-based generator for when Gemini API key is unavailable or offline.
    Maps common analytical questions into valid analytical SQL.
    """
    table_name = schema.get("table_name", "dataset")
    columns = [c["name"] for c in schema.get("columns", [])]
    types_map = {c["name"]: c.get("type", "").lower() for c in schema.get("columns", [])}

    lower_prompt = prompt.lower().strip()

    # Find numeric and categorical columns
    numeric_cols = [
        c for c in columns
        if any(t in types_map.get(c, "") for t in ("int", "float", "double", "decimal", "numeric", "hugeint", "real"))
    ]
    # If types weren't detected as numeric, use common names
    if not numeric_cols:
        numeric_cols = [
            c for c in columns
            if any(k in c.lower() for k in ("amount", "balance", "price", "revenue", "marks", "score", "glucose", "age", "bmi", "attendance", "latency", "cpu", "memory", "gpa", "cost", "total"))
        ]

    cat_cols = [c for c in columns if c not in numeric_cols and not c.lower().endswith("_id")]
    if not cat_cols:
        cat_cols = columns[:2]

    # Heuristic 1: Missing values / NULL check
    if "missing" in lower_prompt or "null" in lower_prompt:
        target_col = columns[0] if columns else "id"
        for col in columns:
            if col.lower() in lower_prompt:
                target_col = col
                break
        sql = f"SELECT * FROM \"{table_name}\" WHERE \"{target_col}\" IS NULL LIMIT 100"
        return {
            "sql": sql,
            "explanation": f"Filtered records from '{table_name}' where column '{target_col}' contains NULL or missing values.",
            "suggested_chart": "table",
            "generator": "heuristic_fallback"
        }

    # Heuristic 2: Attendance below threshold (Education domain)
    if "attendance" in lower_prompt and any(w in lower_prompt for w in ("below", "less", "<", "under")):
        match = re.search(r"(\d+)", lower_prompt)
        threshold = match.group(1) if match else "75"
        att_col = next((c for c in columns if "attendance" in c.lower()), "attendance_pct")
        sql = f"SELECT * FROM \"{table_name}\" WHERE \"{att_col}\" < {threshold} ORDER BY \"{att_col}\" ASC LIMIT 100"
        return {
            "sql": sql,
            "explanation": f"Retrieved students with {att_col} below {threshold}%, ordered from lowest attendance.",
            "suggested_chart": "bar",
            "generator": "heuristic_fallback"
        }

    # Heuristic 3: Incidents by severity (IT domain)
    if "severity" in lower_prompt or "incident" in lower_prompt:
        sev_col = next((c for c in columns if "severity" in c.lower()), "severity")
        sql = f"SELECT \"{sev_col}\", COUNT(*) AS incident_count FROM \"{table_name}\" GROUP BY \"{sev_col}\" ORDER BY incident_count DESC"
        return {
            "sql": sql,
            "explanation": f"Aggregated count of incidents grouped by severity level in descending order.",
            "suggested_chart": "bar",
            "generator": "heuristic_fallback"
        }

    # Heuristic 4: Average glucose or metric by diagnostic/category (Healthcare)
    if "glucose" in lower_prompt or "diagnosis" in lower_prompt:
        diag_col = next((c for c in columns if "diagnos" in c.lower() or "condition" in c.lower()), "diagnosis")
        gluc_col = next((c for c in columns if "glucose" in c.lower() or "blood" in c.lower()), "blood_glucose")
        sql = f"SELECT \"{diag_col}\", ROUND(AVG(\"{gluc_col}\"), 2) AS avg_glucose, COUNT(*) AS patient_count FROM \"{table_name}\" GROUP BY \"{diag_col}\" ORDER BY avg_glucose DESC"
        return {
            "sql": sql,
            "explanation": f"Calculated average glucose levels and patient counts across clinical diagnostic groups.",
            "suggested_chart": "bar",
            "generator": "heuristic_fallback"
        }

    # Heuristic 5: Top categories by amount / revenue / balance (Finance)
    if any(w in lower_prompt for w in ("highest", "top", "largest", "most", "average amount", "revenue")):
        num_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])
        group_col = cat_cols[0] if cat_cols else columns[0]
        match_limit = re.search(r"\b(five|5|ten|10|3|three)\b", lower_prompt)
        limit_val = 5
        if match_limit:
            word = match_limit.group(1).lower()
            limit_val = 10 if word in ("10", "ten") else (3 if word in ("3", "three") else 5)

        sql = (
            f"SELECT \"{group_col}\", "
            f"COUNT(*) AS record_count, "
            f"ROUND(AVG(\"{num_col}\"), 2) AS avg_{num_col}, "
            f"ROUND(SUM(\"{num_col}\"), 2) AS total_{num_col} "
            f"FROM \"{table_name}\" "
            f"GROUP BY \"{group_col}\" "
            f"ORDER BY avg_{num_col} DESC "
            f"LIMIT {limit_val}"
        )
        return {
            "sql": sql,
            "explanation": f"Top {limit_val} categories from '{group_col}' ranked by highest average '{num_col}'.",
            "suggested_chart": "bar",
            "generator": "heuristic_fallback"
        }

    # Heuristic 6: Count by group
    if cat_cols:
        grp = cat_cols[0]
        sql = f"SELECT \"{grp}\", COUNT(*) AS count FROM \"{table_name}\" GROUP BY \"{grp}\" ORDER BY count DESC LIMIT 20"
        return {
            "sql": sql,
            "explanation": f"Count of records grouped by '{grp}' in descending order.",
            "suggested_chart": "bar",
            "generator": "heuristic_fallback"
        }

    # Default fallback: Sample preview
    sql = f"SELECT * FROM \"{table_name}\" LIMIT 50"
    return {
        "sql": sql,
        "explanation": f"Exploratory preview of the first 50 records from table '{table_name}'.",
        "suggested_chart": "table",
        "generator": "heuristic_fallback"
    }


def generate_sql_query(
    prompt: str,
    schema: Dict[str, Any],
    domain: str = "finance"
) -> Dict[str, Any]:
    """
    Translates a natural language instruction into a safe, valid DuckDB SQL query.
    Uses Gemini when GEMINI_API_KEY is configured, else falls back to heuristics.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not gemini_key or not GENAI_AVAILABLE:
        res = _heuristic_sql_fallback(prompt, schema, domain)
        validate_query_safety(res["sql"])
        return res

    # Construct minimal schema metadata to avoid sending sensitive row data
    table_name = schema.get("table_name", "dataset")
    col_summaries = []
    for c in schema.get("columns", []):
        col_summaries.append(f"- {c['name']} ({c.get('type', 'VARCHAR')})")

    columns_str = "\n".join(col_summaries)

    system_instruction = (
        "You are a principal SQL engineer and data architect for DataDock AI. "
        "Your task is to convert natural language instructions into strict, safe, standard DuckDB analytical SQL. "
        "Rules:\n"
        "1. Write ONLY read-only queries (SELECT, WITH).\n"
        "2. Do NOT use DDL or DML statements (no DROP, CREATE, INSERT, UPDATE, DELETE).\n"
        "3. Wrap identifiers in double quotes if they contain spaces or special characters.\n"
        "4. Always apply reasonable LIMITs (e.g. LIMIT 100) when returning unbounded raw rows.\n"
        "5. Return valid JSON only with keys: 'sql' (string), 'explanation' (string), 'suggested_chart' ('bar'|'line'|'pie'|'table')."
    )

    user_content = (
        f"Domain: {domain}\n"
        f"Table name: \"{table_name}\"\n"
        f"Columns:\n{columns_str}\n\n"
        f"User Request: \"{prompt}\"\n\n"
        "Generate the SQL query and return JSON:"
    )

    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )

        response_text = response.text.strip()
        data = json.loads(response_text)
        sql = data.get("sql", "").strip()

        # Validate SQL safety before returning
        validated_sql = validate_query_safety(sql)

        return {
            "sql": validated_sql,
            "explanation": data.get("explanation", "Generated query based on schema and intent."),
            "suggested_chart": data.get("suggested_chart", "table"),
            "generator": "gemini"
        }

    except Exception as e:
        print(f"GEMINI NL-TO-SQL FALLBACK TRIGGERED: {e}")
        fallback_res = _heuristic_sql_fallback(prompt, schema, domain)
        validate_query_safety(fallback_res["sql"])
        return fallback_res


def explain_query_results(
    query: str,
    columns: List[str],
    rows: List[list],
    total_rows: int,
    execution_time_ms: float,
    domain: str = "finance"
) -> Dict[str, Any]:
    """
    Generates a concise, plain-language business/domain explanation of verified SQL query results.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Create grounded evidence summary
    preview_count = min(len(rows), 5)
    sample_preview = rows[:preview_count]

    evidence_summary = (
        f"Query executed in {execution_time_ms} ms. Returned {total_rows} total matching records across {len(columns)} columns.\n"
        f"Columns: {', '.join(columns)}.\n"
    )

    if not gemini_key or not GENAI_AVAILABLE:
        # Deterministic evidence explanation
        summary_lines = [
            f"The query executed successfully in {execution_time_ms}ms, returning {total_rows:,} records.",
            f"Columns analyzed: {', '.join(columns)}."
        ]
        if sample_preview:
            first_row_str = ", ".join(f"{c}: {v}" for c, v in zip(columns[:4], sample_preview[0][:4]))
            summary_lines.append(f"Top result: {first_row_str}")

        return {
            "summary": " ".join(summary_lines),
            "total_rows": total_rows,
            "execution_time_ms": execution_time_ms,
            "generator": "evidence_summary"
        }

    try:
        client = genai.Client(api_key=gemini_key)
        prompt = (
            f"Given the verified SQL execution evidence below, summarize the analytical insight in 2-3 concise sentences for a business user in the {domain} domain.\n"
            f"Do not invent data; strictly use the evidence.\n\n"
            f"SQL: {query}\n"
            f"Evidence: {evidence_summary}\n"
            f"Sample Results: {json.dumps(sample_preview, default=str)}\n"
        )

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=250
            )
        )

        return {
            "summary": response.text.strip(),
            "total_rows": total_rows,
            "execution_time_ms": execution_time_ms,
            "generator": "gemini"
        }

    except Exception as e:
        print(f"GEMINI EXPLAIN FALLBACK: {e}")
        return {
            "summary": f"Executed query successfully in {execution_time_ms}ms with {total_rows:,} matching records.",
            "total_rows": total_rows,
            "execution_time_ms": execution_time_ms,
            "generator": "evidence_summary"
        }
