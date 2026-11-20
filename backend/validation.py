import pandas as pd
from domains import get_rules_for_domain, FINANCIAL_RULES, HEALTHCARE_RULES

DEFAULT_FINANCIAL_RULES = FINANCIAL_RULES

def evaluate_validation_rules(df: pd.DataFrame, domain: str = "finance", custom_rules: list = None) -> dict:
    """
    Evaluates dataset against configured domain validation rules (finance or healthcare).
    Returns structured results with violation counts, violation rates, affected columns, and row-level violation items.
    """
    rules = get_rules_for_domain(domain)
    if custom_rules:
        rules.extend(custom_rules)

    total_rows = len(df)
    results = []
    total_violations = 0
    passed_rules_count = 0
    all_row_violations = []

    if total_rows == 0:
        return {
            "total_rules_evaluated": len(rules),
            "passed_rules_count": len(rules),
            "failed_rules_count": 0,
            "total_violations": 0,
            "overall_compliance_rate": 100.0,
            "rule_results": [],
            "row_violations": []
        }

    for rule in rules:
        rule_id = rule["id"]
        rule_name = rule["name"]
        severity = rule["severity"]
        rule_type = rule["type"]
        keywords = rule.get("target_keywords", [])

        # Find matching columns
        matching_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in keywords):
                matching_cols.append(col)

        rule_failed = False
        rule_violations = 0
        affected_cols_details = []

        for col in matching_cols:
            series = df[col]
            failed_indices = []

            if rule_type == "non_negative":
                num_series = pd.to_numeric(
                    series.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
                    errors="coerce"
                )
                neg_mask = num_series < 0
                failed_indices = list(df.index[neg_mask])

            elif rule_type == "non_null_key":
                null_mask = series.isna() | (series.astype(str).str.strip() == "")
                failed_indices = list(df.index[null_mask])

            elif rule_type == "unique_key":
                dup_mask = series.duplicated(keep=False) & series.notna()
                failed_indices = list(df.index[dup_mask])

            elif rule_type == "allowed_values":
                allowed = [str(v).upper() for v in rule.get("allowed_values", [])]
                str_series = series.dropna().astype(str).str.strip().str.upper()
                invalid_mask = ~str_series.isin(allowed)
                failed_indices = list(str_series.index[invalid_mask])

            elif rule_type == "range_check":
                min_val = rule.get("min_val")
                max_val = rule.get("max_val")
                num_series = pd.to_numeric(
                    series.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
                    errors="coerce"
                )
                mask = pd.Series(False, index=df.index)
                if min_val is not None:
                    mask = mask | (num_series < min_val)
                if max_val is not None:
                    mask = mask | (num_series > max_val)
                failed_indices = list(df.index[mask & num_series.notna()])

            v_count = len(failed_indices)
            if v_count > 0:
                rule_failed = True
                rule_violations += v_count
                sample_failed_vals = [str(v) for v in series.iloc[failed_indices[:5]]]
                affected_cols_details.append({
                    "column": col,
                    "violation_count": v_count,
                    "violation_pct": round((v_count / total_rows) * 100.0, 2),
                    "sample_violations": sample_failed_vals
                })

                # Record individual row violations for row-level inspector (limit to top 50 per rule)
                for idx in failed_indices[:50]:
                    val = str(series.iloc[idx])
                    all_row_violations.append({
                        "row_number": int(idx) + 1,
                        "column": col,
                        "value": val if val != "nan" else "NULL",
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "description": rule.get("description", ""),
                        "severity": severity
                    })

        total_violations += rule_violations
        if rule_failed:
            results.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "description": rule.get("description", ""),
                "severity": severity,
                "passed": False,
                "total_violations": rule_violations,
                "affected_columns_count": len(affected_cols_details),
                "affected_columns": affected_cols_details
            })
        else:
            passed_rules_count += 1
            results.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "description": rule.get("description", ""),
                "severity": severity,
                "passed": True,
                "total_violations": 0,
                "affected_columns_count": 0,
                "affected_columns": []
            })

    total_evaluated = len(results)
    failed_count = total_evaluated - passed_rules_count
    compliance_rate = round((passed_rules_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 100.0

    return {
        "total_rules_evaluated": total_evaluated,
        "passed_rules_count": passed_rules_count,
        "failed_rules_count": failed_count,
        "total_violations": total_violations,
        "overall_compliance_rate": compliance_rate,
        "rule_results": results,
        "row_violations": all_row_violations[:100]
    }

