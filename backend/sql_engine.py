"""
DataDock AI — Safe Analytical SQL Execution Engine
Powered by DuckDB in read-only analytical mode.
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd

from profiler import read_dataset


class SQLSecurityError(Exception):
    """Raised when a query violates safe analytical execution policy."""
    pass


# Disallowed SQL patterns that attempt DDL, DML, file access, or system calls
DISALLOWED_PATTERNS = [
    r"\b(ATTACH|DETACH)\b",
    r"\b(DROP|CREATE|ALTER|TRUNCATE)\b",
    r"\b(INSERT|UPDATE|DELETE|MERGE|REPLACE)\b",
    r"\b(GRANT|REVOKE)\b",
    r"\b(COPY|EXPORT|LOAD|IMPORT)\b",
    r"\b(INSTALL|SET|RESET)\b",
    r"\b(PRAGMA)\b",
    r"\b(READ_PARQUET|WRITE_PARQUET|READ_BLOB)\b",
    r"\b(CALL|EXECUTE|PREPARE|DEALLOCATE)\b",
    r"\b(SYSTEM|SH|SHELL)\b",
    r";.*\S",  # Prevent multiple stacked queries
]

COMPILED_DISALLOWED = [re.compile(p, re.IGNORECASE) for p in DISALLOWED_PATTERNS]


def sanitize_table_name(name: str) -> str:
    """Sanitize a filename or dataset name into a safe SQL identifier."""
    stem = Path(name).stem
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", stem).lower()
    if not safe or safe[0].isdigit():
        safe = f"ds_{safe}"
    return safe[:64]


def validate_query_safety(query: str) -> str:
    """
    Validates that a SQL query is strictly read-only and analytical.
    Returns cleaned SQL string or raises SQLSecurityError.
    """
    if not query or not query.strip():
        raise SQLSecurityError("Query string cannot be empty.")

    cleaned = query.strip().rstrip(";")

    # Check for disallowed keywords/patterns
    for pattern in COMPILED_DISALLOWED:
        if pattern.search(cleaned):
            raise SQLSecurityError(
                f"Query contains disallowed or potentially destructive SQL operation matching security policy."
            )

    # Must start with SELECT or WITH (for CTEs) or EXPLAIN
    tokens = cleaned.split()
    first_token = tokens[0].upper() if tokens else ""
    if first_token not in ("SELECT", "WITH", "EXPLAIN"):
        raise SQLSecurityError(
            f"Only read-only analytical statements (SELECT, WITH) are permitted. Received: {first_token}"
        )

    return cleaned


class DuckDBQueryEngine:
    """
    Analytical SQL engine providing isolated, read-only queries
    over uploaded and sample datasets.
    """

    def __init__(self, upload_dir: Path):
        self.upload_dir = Path(upload_dir)

    def execute_query(
        self,
        query: str,
        dataset_mappings: Dict[str, Path],
        max_rows: int = 2000,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Execute an analytical SQL query against registered datasets.

        dataset_mappings: dict of {safe_table_name: Path_to_csv_or_xlsx}
        """
        validated_sql = validate_query_safety(query)
        start_time = time.perf_counter()

        # Create a fresh, isolated in-memory DuckDB connection for this execution
        conn = duckdb.connect(database=":memory:", read_only=False)

        try:
            # Register all provided datasets as temporary views/tables in DuckDB
            for table_name, file_path in dataset_mappings.items():
                p = Path(file_path)
                if not p.exists():
                    continue

                if p.suffix.lower() == ".csv":
                    # Load directly via DuckDB's high-performance CSV reader
                    escaped_path = str(p.resolve()).replace("\\", "/")
                    conn.execute(
                        f"CREATE VIEW \"{table_name}\" AS SELECT * FROM read_csv_auto('{escaped_path}', ignore_errors=true)"
                    )
                else:
                    # For XLSX or other formats, load via pandas into DuckDB
                    df = read_dataset(p, p.name)
                    conn.register(table_name, df)

            # Limit rows fetched to prevent memory exhaustion, while tracking total count
            count_query = f"SELECT COUNT(*) AS total_count FROM ({validated_sql}) AS __subquery__"
            try:
                count_res = conn.execute(count_query).fetchone()
                total_rows = count_res[0] if count_res else 0
            except Exception:
                # In case COUNT(*) subquery fails for complex CTEs or EXPLAIN, fallback
                total_rows = -1

            # Fetch paginated or bounded rows
            clamped_page = max(1, page)
            clamped_page_size = max(1, min(page_size, 500))
            offset = (clamped_page - 1) * clamped_page_size

            paginated_sql = f"{validated_sql} LIMIT {clamped_page_size} OFFSET {offset}"
            cursor = conn.execute(paginated_sql)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            # Clean rows for JSON serialization
            cleaned_rows = []
            for row in rows:
                cleaned_rows.append([
                    None if val is None or (isinstance(val, float) and pd.isna(val)) else (
                        float(val) if isinstance(val, (float, pd.Float64Dtype)) else (
                            int(val) if isinstance(val, (int, pd.Int64Dtype)) else str(val)
                        )
                    )
                    for val in row
                ])

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # If total_rows wasn't computed accurately, estimate from page
            if total_rows == -1:
                total_rows = len(cleaned_rows)

            return {
                "success": True,
                "sql": validated_sql,
                "execution_time_ms": elapsed_ms,
                "columns": columns,
                "rows": cleaned_rows,
                "row_count": len(cleaned_rows),
                "total_rows": total_rows,
                "page": clamped_page,
                "page_size": clamped_page_size,
                "total_pages": max(1, (total_rows + clamped_page_size - 1) // clamped_page_size) if total_rows >= 0 else 1
            }

        except duckdb.Error as e:
            raise SQLSecurityError(f"SQL Execution Error: {str(e)}")
        except Exception as e:
            raise SQLSecurityError(f"Query Processing Error: {str(e)}")
        finally:
            conn.close()

    def get_dataset_schema(self, file_path: Path, table_name: str) -> Dict[str, Any]:
        """
        Extract schema information (columns, types, sample values) using DuckDB.
        """
        conn = duckdb.connect(database=":memory:", read_only=False)
        p = Path(file_path)
        try:
            if p.suffix.lower() == ".csv":
                escaped_path = str(p.resolve()).replace("\\", "/")
                conn.execute(
                    f"CREATE VIEW \"{table_name}\" AS SELECT * FROM read_csv_auto('{escaped_path}', ignore_errors=true)"
                )
            else:
                df = read_dataset(p, p.name)
                conn.register(table_name, df)

            desc = conn.execute(f"DESCRIBE \"{table_name}\"").fetchall()
            # Sample 3 rows for preview
            sample_rows = conn.execute(f"SELECT * FROM \"{table_name}\" LIMIT 3").fetchall()
            col_names = [d[0] for d in desc]

            columns_info = []
            for idx, col in enumerate(desc):
                col_name = col[0]
                col_type = col[1]
                samples = []
                for s_row in sample_rows:
                    if idx < len(s_row) and s_row[idx] is not None:
                        samples.append(str(s_row[idx]))
                columns_info.append({
                    "name": col_name,
                    "type": str(col_type),
                    "sample_values": samples[:3]
                })

            count_res = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()
            row_count = count_res[0] if count_res else 0

            return {
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(columns_info),
                "columns": columns_info
            }
        finally:
            conn.close()
