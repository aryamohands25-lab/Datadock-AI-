import pandas as pd
import numpy as np
import math
from pathlib import Path


def read_dataset(source, filename=None):
    source_name = filename or getattr(source, "name", source)
    extension = Path(source_name).suffix.lower()

    if extension == ".csv":
        return pd.read_csv(source, low_memory=False)
    if extension == ".xlsx":
        return pd.read_excel(source, engine="openpyxl")

    raise ValueError("Only .csv and .xlsx files are supported.")

def clean_val(val):
    """Ensure value is JSON serializable (convert NaN, Inf, numpy types)."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    return str(val)

def detect_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    else:
        # Check if text could be converted to numeric
        non_nulls = series.dropna().astype(str).str.strip()
        if len(non_nulls) > 0:
            cleaned = non_nulls.str.replace("$", "", regex=False).str.replace(",", "", regex=False)
            try:
                pd.to_numeric(cleaned, errors="raise")
                return "numeric"
            except (ValueError, TypeError):
                pass
        return "text"

def profile_dataframe(df: pd.DataFrame):
    total_rows = len(df)
    total_cols = len(df.columns)
    
    if total_rows == 0:
        return {
            "total_rows": 0,
            "total_columns": total_cols,
            "completeness_score": 100.0,
            "duplicate_rows": 0,
            "columns": {}
        }

    total_cells = total_rows * total_cols
    non_null_cells = df.notna().sum().sum()
    completeness_score = round((non_null_cells / total_cells) * 100.0, 2) if total_cells > 0 else 100.0
    duplicate_rows = int(df.duplicated().sum())

    cols_profile = {}
    for col in df.columns:
        series = df[col]
        col_type = detect_column_type(series)
        null_count = int(series.isna().sum())
        null_pct = round((null_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))

        sample_vals = [clean_val(v) for v in series.dropna().unique()[:5]]

        col_dict = {
            "data_type": col_type,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "sample_values": sample_vals,
            "is_financial_numeric": (col_type == "numeric"),
            "sum": None,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "zero_count": 0,
            "negative_count": 0
        }

        if col_type == "numeric":
            # Coerce to numeric for stats
            num_series = pd.to_numeric(
                series.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
                errors="coerce"
            ).dropna()
            
            if len(num_series) > 0:
                col_dict["sum"] = clean_val(num_series.sum())
                col_dict["mean"] = clean_val(num_series.mean())
                col_dict["median"] = clean_val(num_series.median())
                col_dict["min"] = clean_val(num_series.min())
                col_dict["max"] = clean_val(num_series.max())
                col_dict["std"] = clean_val(num_series.std()) if len(num_series) > 1 else 0.0
                col_dict["zero_count"] = int((num_series == 0).sum())
                col_dict["negative_count"] = int((num_series < 0).sum())

        cols_profile[str(col)] = col_dict

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "completeness_score": completeness_score,
        "duplicate_rows": duplicate_rows,
        "columns": cols_profile
    }

def compare_csv_files(file_a_path: str, file_b_path: str, name_a: str, name_b: str, key_column: str = None):
    try:
        df_a = read_dataset(file_a_path, name_a)
    except Exception as e:
        raise ValueError(f"Failed to read Baseline dataset ({name_a}): {str(e)}")

    try:
        df_b = read_dataset(file_b_path, name_b)
    except Exception as e:
        raise ValueError(f"Failed to read Comparison dataset ({name_b}): {str(e)}")

    prof_a = profile_dataframe(df_a)
    prof_b = profile_dataframe(df_b)

    cols_a = list(df_a.columns)
    cols_b = list(df_b.columns)

    set_a = set(cols_a)
    set_b = set(cols_b)

    only_a = sorted(list(set_a - set_b))
    only_b = sorted(list(set_b - set_a))
    common_cols = [c for c in cols_a if c in set_b]

    # Check data type mismatches in common columns
    type_mismatches = []
    for c in common_cols:
        type_a = prof_a["columns"][c]["data_type"]
        type_b = prof_b["columns"][c]["data_type"]
        if type_a != type_b:
            type_mismatches.append({
                "column": c,
                "type_a": type_a,
                "type_b": type_b
            })

    schema_drift = {
        "columns_only_in_a": only_a,
        "columns_only_in_b": only_b,
        "common_columns": common_cols,
        "type_mismatches": type_mismatches,
        "has_drift": bool(len(only_a) > 0 or len(only_b) > 0 or len(type_mismatches) > 0)
    }

    # Column Comparison Table
    all_columns_ordered = cols_a + [c for c in cols_b if c not in set_a]
    column_comparison = []

    for c in all_columns_ordered:
        in_a = c in set_a
        in_b = c in set_b

        info_a = prof_a["columns"].get(c, {})
        info_b = prof_b["columns"].get(c, {})

        type_a = info_a.get("data_type", "-")
        type_b = info_b.get("data_type", "-")

        null_pct_a = info_a.get("null_pct", None)
        null_pct_b = info_b.get("null_pct", None)

        unique_a = info_a.get("unique_count", None)
        unique_b = info_b.get("unique_count", None)

        if not in_b:
            status = "Removed in B"
        elif not in_a:
            status = "Added in B"
        elif type_a != type_b:
            status = "Type Mismatch"
        else:
            status = "Matched"

        column_comparison.append({
            "column": c,
            "in_a": in_a,
            "in_b": in_b,
            "type_a": type_a,
            "type_b": type_b,
            "null_pct_a": null_pct_a,
            "null_pct_b": null_pct_b,
            "unique_a": unique_a,
            "unique_b": unique_b,
            "status": status
        })

    # Financial Metrics Comparison (numeric columns in common)
    financial_comparison = []
    for c in common_cols:
        col_a_info = prof_a["columns"][c]
        col_b_info = prof_b["columns"][c]

        if col_a_info["data_type"] == "numeric" or col_b_info["data_type"] == "numeric":
            sum_a = col_a_info.get("sum") or 0.0
            sum_b = col_b_info.get("sum") or 0.0
            sum_delta = clean_val(sum_b - sum_a)
            sum_pct_change = clean_val(((sum_b - sum_a) / abs(sum_a) * 100.0)) if sum_a != 0 else (0.0 if sum_b == 0 else 100.0)

            mean_a = col_a_info.get("mean") or 0.0
            mean_b = col_b_info.get("mean") or 0.0
            mean_delta = clean_val(mean_b - mean_a)

            median_a = col_a_info.get("median") or 0.0
            median_b = col_b_info.get("median") or 0.0
            median_delta = clean_val(median_b - median_a)

            std_a = col_a_info.get("std") or 0.0
            std_b = col_b_info.get("std") or 0.0
            std_delta = clean_val(std_b - std_a)

            zero_count_a = col_a_info.get("zero_count", 0)
            zero_count_b = col_b_info.get("zero_count", 0)
            negative_count_a = col_a_info.get("negative_count", 0)
            negative_count_b = col_b_info.get("negative_count", 0)

            financial_comparison.append({
                "column": c,
                "sum_a": sum_a,
                "sum_b": sum_b,
                "sum_delta": sum_delta,
                "sum_pct_change": sum_pct_change,
                "mean_a": mean_a,
                "mean_b": mean_b,
                "mean_delta": mean_delta,
                "median_a": median_a,
                "median_b": median_b,
                "median_delta": median_delta,
                "min_a": col_a_info.get("min"),
                "min_b": col_b_info.get("min"),
                "max_a": col_a_info.get("max"),
                "max_b": col_b_info.get("max"),
                "std_a": std_a,
                "std_b": std_b,
                "std_delta": std_delta,
                "zero_count_a": zero_count_a,
                "zero_count_b": zero_count_b,
                "zero_count_delta": zero_count_b - zero_count_a,
                "negative_count_a": negative_count_a,
                "negative_count_b": negative_count_b,
                "negative_count_delta": negative_count_b - negative_count_a
            })

    # Row Discrepancy & Row-level Matching
    row_delta = prof_b["total_rows"] - prof_a["total_rows"]
    row_delta_pct = round((row_delta / prof_a["total_rows"] * 100.0), 2) if prof_a["total_rows"] > 0 else 0.0

    # Auto detect key column if not explicitly given
    if not key_column:
        potential_keys = [c for c in common_cols if "id" in c.lower() or "code" in c.lower() or "num" in c.lower() or "key" in c.lower()]
        if potential_keys:
            key_column = potential_keys[0]

    sample_diffs = []
    matched_keys_count = 0
    missing_in_b = 0
    added_in_b = 0

    if key_column and key_column in df_a.columns and key_column in df_b.columns:
        try:
            df_a_indexed = df_a.drop_duplicates(subset=[key_column]).set_index(key_column)
            df_b_indexed = df_b.drop_duplicates(subset=[key_column]).set_index(key_column)

            keys_a = set(df_a_indexed.index)
            keys_b = set(df_b_indexed.index)

            common_keys = list(keys_a.intersection(keys_b))
            matched_keys_count = len(common_keys)
            missing_in_b = len(keys_a - keys_b)
            added_in_b = len(keys_b - keys_a)

            # Check value diffs in top common keys
            diff_count = 0
            for k in common_keys:
                if diff_count >= 25:
                    break
                row_a = df_a_indexed.loc[k]
                row_b = df_b_indexed.loc[k]

                for c in common_cols:
                    if c == key_column:
                        continue
                    val_a = clean_val(row_a[c])
                    val_b = clean_val(row_b[c])
                    if val_a != val_b:
                        sample_diffs.append({
                            "key": str(k),
                            "column": c,
                            "val_a": val_a,
                            "val_b": val_b
                        })
                        diff_count += 1
                        if diff_count >= 25:
                            break
        except Exception as err:
            print("Row indexing error:", err)

    row_discrepancies = {
        "key_column_used": key_column,
        "matched_keys_count": matched_keys_count,
        "missing_in_b_count": missing_in_b,
        "added_in_b_count": added_in_b,
        "sample_value_diffs": sample_diffs
    }

    # Data Quality Scores
    score_a = round((prof_a["completeness_score"] * 0.7) + ((1 - (prof_a["duplicate_rows"] / (prof_a["total_rows"] or 1))) * 30), 1)
    score_b = round((prof_b["completeness_score"] * 0.7) + ((1 - (prof_b["duplicate_rows"] / (prof_b["total_rows"] or 1))) * 30), 1)

    return {
        "summary": {
            "name_a": name_a,
            "name_b": name_b,
            "rows_a": prof_a["total_rows"],
            "rows_b": prof_b["total_rows"],
            "cols_a": prof_a["total_columns"],
            "cols_b": prof_b["total_columns"],
            "duplicates_a": prof_a["duplicate_rows"],
            "duplicates_b": prof_b["duplicate_rows"],
            "completeness_a": prof_a["completeness_score"],
            "completeness_b": prof_b["completeness_score"],
            "quality_score_a": max(0.0, min(100.0, score_a)),
            "quality_score_b": max(0.0, min(100.0, score_b)),
            "row_delta": row_delta,
            "row_delta_pct": row_delta_pct
        },
        "schema_drift": schema_drift,
        "column_comparison": column_comparison,
        "financial_metrics": financial_comparison,
        "row_discrepancies": row_discrepancies
    }
