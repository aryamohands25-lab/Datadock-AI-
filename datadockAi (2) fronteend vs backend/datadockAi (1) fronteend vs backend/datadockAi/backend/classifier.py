def classify_dataset_regressions(comparison_data: dict, validation_a: dict = None, validation_b: dict = None) -> dict:
    """
    Classifies changes between Version A (Baseline) and Version B (Target) into four categories:
    - REGRESSION (🔴)
    - IMPROVEMENT (🟢)
    - NEUTRAL (⚪)
    - REQUIRES_HUMAN_REVIEW (🟡)
    """
    items = []

    summary = comparison_data.get("summary", {})
    drift = comparison_data.get("schema_drift", {})
    cols = comparison_data.get("column_comparison", [])
    financials = comparison_data.get("financial_metrics", [])
    rows = comparison_data.get("row_discrepancies", {})

    # 1. Quality Score Change
    q_a = summary.get("quality_score_a", 100.0)
    q_b = summary.get("quality_score_b", 100.0)
    q_delta = round(q_b - q_a, 1)

    if q_delta < -2.0:
        items.append({
            "category": "REGRESSION",
            "title": "Overall Quality Score Decreased",
            "details": f"Quality score dropped by {abs(q_delta)} points ({q_a}% → {q_b}%).",
            "severity": "HIGH"
        })
    elif q_delta > 2.0:
        items.append({
            "category": "IMPROVEMENT",
            "title": "Overall Quality Score Improved",
            "details": f"Quality score increased by {q_delta} points ({q_a}% → {q_b}%).",
            "severity": "INFO"
        })

    # 2. Duplicate Row Changes
    dups_a = summary.get("duplicates_a", 0)
    dups_b = summary.get("duplicates_b", 0)
    dup_delta = dups_b - dups_a

    if dup_delta > 0:
        items.append({
            "category": "REGRESSION",
            "title": "New Duplicate Rows Introduced",
            "details": f"Duplicate rows increased from {dups_a} to {dups_b} (+{dup_delta}).",
            "severity": "HIGH"
        })
    elif dup_delta < 0:
        items.append({
            "category": "IMPROVEMENT",
            "title": "Duplicate Rows Cleared",
            "details": f"Duplicate rows reduced from {dups_a} to {dups_b} ({dup_delta}).",
            "severity": "INFO"
        })

    # 3. Schema Drift Analysis
    if drift.get("has_drift"):
        cols_removed = drift.get("columns_only_in_a", [])
        cols_added = drift.get("columns_only_in_b", [])
        type_mismatches = drift.get("type_mismatches", [])

        if cols_removed:
            items.append({
                "category": "REQUIRES_HUMAN_REVIEW",
                "title": "Columns Removed in Target Version",
                "details": f"Columns removed: {', '.join(cols_removed)}",
                "severity": "HIGH"
            })
        if cols_added:
            items.append({
                "category": "REQUIRES_HUMAN_REVIEW",
                "title": "New Columns Added in Target Version",
                "details": f"New columns added: {', '.join(cols_added)}",
                "severity": "MEDIUM"
            })
        if type_mismatches:
            for tm in type_mismatches:
                items.append({
                    "category": "REGRESSION",
                    "title": f"Data Type Mismatch: {tm['column']}",
                    "details": f"Column '{tm['column']}' changed data type from {tm['type_a']} to {tm['type_b']}.",
                    "severity": "CRITICAL"
                })

    # 4. Null Rate Regressions / Improvements per Column
    for c in cols:
        null_a = c.get("null_pct_a")
        null_b = c.get("null_pct_b")
        if null_a is not None and null_b is not None:
            null_delta = round(null_b - null_a, 2)
            if null_delta >= 5.0:
                items.append({
                    "category": "REGRESSION",
                    "title": f"Missing Values Increased: {c['column']}",
                    "details": f"Null rate increased by {null_delta}% ({null_a}% → {null_b}%).",
                    "severity": "HIGH" if null_delta >= 15.0 else "MEDIUM"
                })
            elif null_delta <= -5.0:
                items.append({
                    "category": "IMPROVEMENT",
                    "title": f"Completeness Improved: {c['column']}",
                    "details": f"Null rate decreased by {abs(null_delta)}% ({null_a}% → {null_b}%).",
                    "severity": "INFO"
                })

    # 5. Financial Summary Shifts & Negative Amount Anomaly Checks
    for f in financials:
        pct_change = f.get("sum_pct_change")
        if pct_change is not None and abs(pct_change) >= 20.0:
            items.append({
                "category": "REQUIRES_HUMAN_REVIEW",
                "title": f"Significant Financial Metric Shift: {f['column']}",
                "details": f"Total sum shifted by {pct_change}% (Base: {f['sum_a']:,} → Target: {f['sum_b']:,}).",
                "severity": "MEDIUM"
            })

        neg_a = f.get("negative_count_a", 0)
        neg_b = f.get("negative_count_b", 0)
        if neg_b > neg_a:
            items.append({
                "category": "REGRESSION",
                "title": f"Negative Value Anomaly: {f['column']}",
                "details": f"Negative values increased from {neg_a} to {neg_b} (+{neg_b - neg_a}).",
                "severity": "HIGH"
            })

    # 6. Validation Rule Compliance Comparison
    if validation_a and validation_b:
        comp_a = validation_a.get("overall_compliance_rate", 100.0)
        comp_b = validation_b.get("overall_compliance_rate", 100.0)
        comp_delta = round(comp_b - comp_a, 1)

        if comp_delta < 0:
            items.append({
                "category": "REGRESSION",
                "title": "Validation Rule Compliance Dropped",
                "details": f"Rule compliance rate dropped from {comp_a}% to {comp_b}%.",
                "severity": "HIGH"
            })
        elif comp_delta > 0:
            items.append({
                "category": "IMPROVEMENT",
                "title": "Validation Rule Compliance Improved",
                "details": f"Rule compliance rate increased from {comp_a}% to {comp_b}%.",
                "severity": "INFO"
            })

        # New Rule Failures
        rules_a_failed = {r["rule_id"] for r in validation_a.get("rule_results", []) if not r["passed"]}
        rules_b_failed = {r["rule_id"]: r for r in validation_b.get("rule_results", []) if not r["passed"]}

        new_failures = [r_id for r_id in rules_b_failed if r_id not in rules_a_failed]
        for nf in new_failures:
            r = rules_b_failed[nf]
            items.append({
                "category": "REGRESSION",
                "title": f"New Rule Violation: {r['rule_name']}",
                "details": f"Rule failed in target version with {r['total_violations']} violations across {r['affected_columns_count']} columns.",
                "severity": r.get("severity", "HIGH")
            })

    # 7. Row Key Matching Discrepancies
    if rows.get("missing_in_b_count", 0) > 0:
        items.append({
            "category": "REGRESSION",
            "title": "Baseline Primary Keys Missing in Target",
            "details": f"{rows['missing_in_b_count']} primary key records from Baseline were missing in Target.",
            "severity": "HIGH"
        })

    # If no major items detected, add neutral label
    if not items:
        items.append({
            "category": "NEUTRAL",
            "title": "No Significant Quality Regressions",
            "details": "Target dataset maintains quality metrics and schema consistency relative to Baseline.",
            "severity": "INFO"
        })

    # Count categories
    counts = {
        "REGRESSION": sum(1 for i in items if i["category"] == "REGRESSION"),
        "IMPROVEMENT": sum(1 for i in items if i["category"] == "IMPROVEMENT"),
        "NEUTRAL": sum(1 for i in items if i["category"] == "NEUTRAL"),
        "REQUIRES_HUMAN_REVIEW": sum(1 for i in items if i["category"] == "REQUIRES_HUMAN_REVIEW")
    }

    overall_status = "REGRESSION" if counts["REGRESSION"] > 0 else (
        "REQUIRES_HUMAN_REVIEW" if counts["REQUIRES_HUMAN_REVIEW"] > 0 else (
            "IMPROVEMENT" if counts["IMPROVEMENT"] > 0 else "NEUTRAL"
        )
    )

    return {
        "overall_status": overall_status,
        "counts": counts,
        "classifications": items
    }
