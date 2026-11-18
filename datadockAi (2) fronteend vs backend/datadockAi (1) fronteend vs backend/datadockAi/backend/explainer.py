import json
import os
from urllib.request import Request, urlopen


def generate_audit_explanation(comparison_data: dict, classification: dict, validation_a: dict = None, validation_b: dict = None, domain: str = "finance") -> dict:
    """
    Produces a domain-aware, plain-language, evidence-grounded data audit explanation summary
    strictly based on deterministic findings from profiler, validation, and classifier modules.
    """
    domain_clean = str(domain).lower().strip()
    is_healthcare = domain_clean in ("healthcare", "health")
    is_academics = domain_clean in ("academics", "education", "academic")
    is_software = domain_clean in ("software_systems", "it", "software", "it_software", "it_systems")

    if is_healthcare:
        domain_title = "Healthcare Clinical"
    elif is_academics:
        domain_title = "Academic & Education"
    elif is_software:
        domain_title = "IT & Software Systems"
    else:
        domain_title = "Financial"

    summary = comparison_data.get("summary", {})
    drift = comparison_data.get("schema_drift", {})
    cols = comparison_data.get("column_comparison", [])
    financials = comparison_data.get("financial_metrics", [])
    status = classification.get("overall_status", "NEUTRAL")
    classifications = classification.get("classifications", [])

    name_a = summary.get("name_a", "Baseline CSV")
    name_b = summary.get("name_b", "Comparison CSV")

    paragraphs = []

    # 1. Executive Headline & Domain Narrative
    if status == "REGRESSION":
        headline = f"⚠️ {domain_title} Data Quality Regression Detected between '{name_a}' and '{name_b}'"
        if is_healthcare:
            domain_context_text = "This change may affect clinical diagnosis models, patient safety monitoring, and EHR data integrity. Immediate review of data intake pipeline is recommended."
        elif is_academics:
            domain_context_text = "This change may impact student transcript accuracy, academic standing calculations, GPA distributions, and accreditation compliance. Immediate review of student records is recommended."
        elif is_software:
            domain_context_text = "This change may impact production system SLAs, infrastructure monitoring reliability, and service uptime. Immediate review of system telemetry pipeline is recommended."
        else:
            domain_context_text = "Immediate review is recommended before using this dataset version in financial reporting, risk models, or downstream ledger ingestion."

        paragraphs.append(
            f"Automated audit revealed critical quality regressions in '{name_b}' compared to baseline dataset '{name_a}'. "
            f"Overall quality score shifted from {summary.get('quality_score_a')}% to {summary.get('quality_score_b')}%. "
            f"{domain_context_text}"
        )
    elif status == "REQUIRES_HUMAN_REVIEW":
        headline = f"🔍 Human Review Recommended for {domain_title} Dataset Version '{name_b}'"
        paragraphs.append(
            f"The version comparison identified structural or statistical shifts between '{name_a}' and '{name_b}'. "
            f"While quality scores remain acceptable ({summary.get('quality_score_b')}%), schema drift or measurement metric shifts require verification."
        )
    elif status == "IMPROVEMENT":
        headline = f"✅ {domain_title} Data Quality Improvement Verified in '{name_b}'"
        paragraphs.append(
            f"Target version '{name_b}' shows measurable quality improvements over baseline '{name_a}', "
            f"with quality score rising from {summary.get('quality_score_a')}% to {summary.get('quality_score_b')}%."
        )
    else:
        headline = f"ℹ️ Datasets Verified Stable with No Critical Regressions"
        paragraphs.append(
            f"Comparison between '{name_a}' ({summary.get('rows_a'):,} rows) and '{name_b}' ({summary.get('rows_b'):,} rows) "
            f"shows consistent quality score ({summary.get('quality_score_b')}%) and schema alignment."
        )

    # 2. Key Regressions & Risk Evidence
    regressions = [c for c in classifications if c["category"] == "REGRESSION"]
    if regressions:
        reg_bullets = [f"• {r['title']}: {r['details']}" for r in regressions[:4]]
        paragraphs.append(
            "Key Regressions Identified:\n" + "\n".join(reg_bullets)
        )

    # 3. Numeric Metrics & Schema Drift Summary
    fin_notes = []
    curr_prefix = "₹" if (not is_healthcare and not is_academics and not is_software) else ""
    for f in financials:
        if abs(f.get("sum_pct_change", 0)) >= 10.0:
            fin_notes.append(f"Field '{f['column']}' total sum changed by {f['sum_pct_change']}% (Base: {curr_prefix}{f['sum_a']:,.2f} → Target: {curr_prefix}{f['sum_b']:,.2f}).")

    if drift.get("has_drift"):
        drift_desc = []
        if drift.get("columns_only_in_a"):
            drift_desc.append(f"removed columns ({', '.join(drift['columns_only_in_a'])})")
        if drift.get("columns_only_in_b"):
            drift_desc.append(f"added columns ({', '.join(drift['columns_only_in_b'])})")
        paragraphs.append(
            f"Schema Drift Notice: Version '{name_b}' has {', '.join(drift_desc)}. "
            f"{' '.join(fin_notes)}"
        )
    elif fin_notes:
        metric_label = "Clinical Lab Metrics" if is_healthcare else ("Academic Metrics" if is_academics else ("System Telemetry Metrics" if is_software else "Financial Metrics"))
        paragraphs.append(f"{metric_label} Shift: " + " ".join(fin_notes))

    # 4. Actionable Recommendations
    recommendations = []
    if any(c["category"] == "REGRESSION" for c in classifications):
        if is_healthcare:
            recommendations.append("Investigate missing biomarker measurements (e.g. Glucose/BMI) or duplicate Patient IDs before medical analytics ingestion.")
        elif is_academics:
            recommendations.append("Audit out-of-range GPA or exam scores and resolve duplicate Student IDs before submitting institutional accreditation reports or grade point averages.")
        elif is_software:
            recommendations.append("Investigate latency spikes, out-of-range CPU/memory telemetry, or duplicate Incident IDs before deploying production release or updating monitoring dashboards.")
        else:
            recommendations.append("Investigate missing key records or null value increases before downstream financial export.")
    if drift.get("columns_only_in_a"):
        schema_type = "clinical patient" if is_healthcare else ("student record" if is_academics else ("system telemetry" if is_software else "reporting"))
        recommendations.append(f"Confirm whether removed baseline columns affect {schema_type} schemas.")
    if validation_b and validation_b.get("failed_rules_count", 0) > 0:
        recommendations.append(f"Resolve {validation_b['failed_rules_count']} failing validation rule(s) in target dataset.")
    if not recommendations:
        recommendations.append("Dataset version is clean and cleared for downstream processing.")

    explanation = {
        "headline": headline,
        "overall_status": status,
        "domain": domain_clean,
        "executive_summary": "\n\n".join(paragraphs),
        "recommended_actions": recommendations,
        "grounded_evidence": {
            "total_regressions": len(regressions),
            "quality_score_delta": round(summary.get("quality_score_b", 100) - summary.get("quality_score_a", 100), 1),
            "row_count_delta": summary.get("row_delta", 0),
            "schema_drift_detected": drift.get("has_drift", False)
        },
        "generator": "rules_fallback"
    }

    return _enhance_with_openai(
        explanation,
        comparison_data,
        classification,
        validation_a,
        validation_b,
        domain_clean
    )


def _enhance_with_openai(explanation, comparison_data, classification, validation_a, validation_b, domain):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return explanation

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    summary = comparison_data.get("summary", {})
    drift = comparison_data.get("schema_drift", {})

    def validation_evidence(validation):
        if not validation:
            return None
        return {
            "overall_compliance_rate": validation.get("overall_compliance_rate"),
            "failed_rules_count": validation.get("failed_rules_count"),
            "rule_results": [
                {
                    "rule_name": rule.get("rule_name"),
                    "passed": rule.get("passed"),
                    "total_violations": rule.get("total_violations")
                }
                for rule in validation.get("rule_results", [])[:8]
            ]
        }

    evidence = {
        "domain": domain,
        "status": classification.get("overall_status"),
        "summary": {
            key: summary.get(key)
            for key in (
                "name_a", "name_b", "rows_a", "rows_b", "row_delta",
                "cols_a", "cols_b", "quality_score_a", "quality_score_b",
                "duplicates_a", "duplicates_b"
            )
        },
        "schema_drift": {
            "has_drift": drift.get("has_drift"),
            "columns_only_in_a": drift.get("columns_only_in_a", []),
            "columns_only_in_b": drift.get("columns_only_in_b", []),
            "type_mismatches": drift.get("type_mismatches", [])
        },
        "findings": classification.get("classifications", [])[:12],
        "validation_a": validation_evidence(validation_a),
        "validation_b": validation_evidence(validation_b)
    }

    prompt = (
        "Explain this data-quality comparison to a non-technical business user in plain, direct language. "
        "Keep the executive summary under 120 words and format it as four short labeled lines: "
        "Bottom line:, What changed:, Why it matters:, What to do next:. "
        "Use exact counts and percentages from the evidence when available. Briefly explain technical terms, "
        "such as schema drift, the first time they appear. Separate observed facts from possible impacts; "
        "never claim a cause or business/clinical impact that the evidence does not establish. "
        "Keep the headline short and aligned with the supplied status. If status is NEUTRAL, clearly say "
        "that no significant regressions were detected. Recommend only practical actions supported by the findings. "
        "Do not invent metrics or findings, change the audit status, or expose row-level or personal data. "
        "Return JSON with exactly these fields: headline (string), executive_summary (string), "
        "recommended_actions (array of 1 to 3 strings).\n\n"
        f"Evidence:\n{json.dumps(evidence, ensure_ascii=False, default=str)}"
    )
    request_data = json.dumps({
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a clear, careful data-quality analyst. Explain findings for busy non-technical decision makers, and ground every statement in the supplied evidence."},
            {"role": "user", "content": prompt}
        ],
        "options": {"temperature": 0.1}
    }).encode("utf-8")

    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(request, timeout=45) as response:
            llm_response = json.loads(response.read().decode("utf-8"))
        generated = json.loads(llm_response["choices"][0]["message"]["content"])

        headline = generated.get("headline")
        executive_summary = generated.get("executive_summary")
        actions = generated.get("recommended_actions")
        if not isinstance(headline, str) or not isinstance(executive_summary, str) or not isinstance(actions, list):
            return explanation
        if not headline.strip() or not executive_summary.strip():
            return explanation

        explanation.update({
            "headline": headline.strip()[:300],
            "executive_summary": executive_summary.strip()[:4000],
            "recommended_actions": [action.strip()[:500] for action in actions if isinstance(action, str) and action.strip()][:4],
            "generator": "openai",
            "model": model
        })
    except Exception as error:
        print(f"OPENAI EXPLANATION UNAVAILABLE: {error}")

    return explanation
