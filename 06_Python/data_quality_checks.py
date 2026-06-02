"""
data_quality_checks.py
======================
Phase 8 -- Python Enhancement Layer
FinTech Financial Operations Control & Reconciliation System

Purpose:
    Runs reusable data-quality checks across Phase 3-7 CSV files.  Detects
    missing fields, duplicate records, invalid dates, non-numeric amounts,
    missing account IDs, invalid statuses, and null critical fields.
    One output row is written per check (pass or fail) so the summary
    shows an accurate checks-run count and a meaningful pass rate.

Business context:
    Before any reconciliation, exception review, or reporting step can be
    trusted, the underlying data must be clean.  This script acts as a
    programmatic data-quality gate, catching issues that would otherwise
    surface as silent errors or misleading numbers in Excel and Power BI.

Inputs:
    - 02_Data/custodian_balances.csv
    - 02_Data/reconciliation_breaks.csv
    - 02_Data/exception_log.csv
    - 02_Data/vendor_files.csv
    - 02_Data/raw_stock_transactions.csv

Outputs:
    - 06_Python/outputs/data_quality_results.csv
"""

import pandas as pd
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "02_Data"
OUTPUT_DIR   = PROJECT_ROOT / "06_Python" / "outputs"

# Files to validate with their key column definitions
FILES_TO_CHECK = {
    "custodian_balances.csv": {
        "required_cols":  ["custodian_balance_id", "account_id", "balance_date",
                           "custodian_cash_balance", "currency"],
        "id_cols":        ["custodian_balance_id"],
        "date_cols":      ["balance_date"],
        "numeric_cols":   ["custodian_cash_balance"],
        "valid_statuses": {},
    },
    "reconciliation_breaks.csv": {
        "required_cols":     ["break_id", "account_id", "business_date",
                              "break_category", "dollar_exposure", "variance"],
        "id_cols":           ["break_id"],
        "date_cols":         ["business_date"],
        "numeric_cols":      ["internal_value", "custodian_value", "variance", "dollar_exposure"],
        "valid_statuses":    {"break_category": ["CASH_BALANCE_BREAK", "SHARE_QUANTITY_BREAK"]},
        "critical_null_cols": ["account_id", "break_category", "dollar_exposure"],
    },
    "exception_log.csv": {
        "required_cols":     ["exception_id", "account_id", "business_date", "break_type",
                              "severity", "variance_amount", "root_cause", "status"],
        "id_cols":           ["exception_id"],
        "date_cols":         ["business_date", "detected_date", "due_date"],
        "numeric_cols":      ["variance_amount", "dollar_exposure", "aging_days"],
        "valid_statuses":    {
            "severity": ["HIGH", "MEDIUM", "LOW"],
            "status":   ["OPEN", "IN_REVIEW", "PENDING_VENDOR", "RESOLVED"],
        },
        "critical_null_cols": ["account_id", "severity", "root_cause", "status"],
    },
    "vendor_files.csv": {
        "required_cols":  ["source_file_id", "file_name", "source_system",
                           "receipt_status", "record_count", "expected_date"],
        "id_cols":        ["source_file_id"],
        "date_cols":      ["expected_date"],
        "numeric_cols":   ["record_count", "control_total"],
        "valid_statuses": {
            "receipt_status":    ["RECEIVED", "MISSING"],
            "validation_status": ["VALIDATED", "FAILED", "PENDING"],
        },
    },
    "raw_stock_transactions.csv": {
        "required_cols":  ["ID", "Transaction Date", "Ticker", "No. of shares", "Price / share"],
        "id_cols":        ["ID"],
        "date_cols":      ["Transaction Date"],
        "numeric_cols":   ["No. of shares", "Price / share"],
        "valid_statuses": {},
    },
}

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def load_csv_safe(path: Path) -> pd.DataFrame | None:
    """Load a CSV without crashing on missing files."""
    if not path.exists():
        print(f"  [SKIP] Not found: {path.name}")
        return None
    return pd.read_csv(path, low_memory=False)


def make_result(
    check_id: int,
    input_file: str,
    check_name: str,
    check_status: str,      # "PASS" or "FAIL"
    failed_record_count: int,
    severity: str,
    issue_description: str,
    suggested_fix: str,
) -> dict:
    """Build a single quality-check result row."""
    return {
        "check_id":            check_id,
        "input_file":          input_file,
        "check_name":          check_name,
        "check_status":        check_status,
        "failed_record_count": failed_record_count,
        "severity":            severity,
        "issue_description":   issue_description,
        "suggested_fix":       suggested_fix,
    }


# ─────────────────────────────────────────────
# REUSABLE CHECK FUNCTIONS
# Each returns a list of result dicts (one per check performed).
# A PASS row is also emitted so the summary shows true checks_run.
# ─────────────────────────────────────────────

def check_missing_required_fields(
    df: pd.DataFrame, required_cols: list[str], fname: str, ctr: list
) -> list[dict]:
    """Flag required columns that are absent or contain nulls.

    Business rationale: A missing field means a downstream formula, SQL join,
    or report filter will silently fail or produce incorrect totals.
    """
    results = []
    for col in required_cols:
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns:
            results.append(make_result(cid, fname, "MISSING_COLUMN", "FAIL",
                len(df), "HIGH",
                f"Required column '{col}' is absent from {fname}",
                f"Confirm source query/export includes '{col}'"))
        else:
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                pct = 100 * null_count / len(df)
                sev = "HIGH" if pct > 10 else "MEDIUM"
                results.append(make_result(cid, fname, "NULL_REQUIRED_FIELD", "FAIL",
                    null_count, sev,
                    f"'{col}' has {null_count:,} null values ({pct:.1f}% of rows) in {fname}",
                    f"Investigate upstream source for missing '{col}' values"))
            else:
                results.append(make_result(cid, fname, "NULL_REQUIRED_FIELD", "PASS",
                    0, "INFO", f"'{col}' — no nulls found", "No action required"))
    return results


def check_duplicate_ids(
    df: pd.DataFrame, id_cols: list[str], fname: str, ctr: list
) -> list[dict]:
    """Flag duplicate values in primary key / ID columns.

    Business rationale: Duplicate IDs cause double-counting in reconciliation
    totals and exception tallies, distorting management reports.
    """
    results = []
    for col in id_cols:
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns:
            results.append(make_result(cid, fname, "DUPLICATE_ID", "FAIL",
                0, "HIGH", f"ID column '{col}' not found in {fname}",
                f"Ensure '{col}' is exported from the source"))
            continue
        dup_count = int(df.duplicated(subset=[col], keep=False).sum())
        if dup_count > 0:
            results.append(make_result(cid, fname, "DUPLICATE_ID", "FAIL",
                dup_count, "HIGH",
                f"'{col}' contains {dup_count:,} duplicate values in {fname}",
                f"Deduplicate on '{col}'; investigate source for re-sends or join issues"))
        else:
            results.append(make_result(cid, fname, "DUPLICATE_ID", "PASS",
                0, "INFO", f"'{col}' — no duplicates found", "No action required"))
    return results


def check_invalid_dates(
    df: pd.DataFrame, date_cols: list[str], fname: str, ctr: list
) -> list[dict]:
    """Flag rows where date columns cannot be parsed as valid dates.

    Business rationale: Invalid dates block SLA calculations, aging logic,
    and date-range filters in SQL, Excel, and Power BI.
    """
    results = []
    for col in date_cols:
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns:
            results.append(make_result(cid, fname, "INVALID_DATE", "FAIL",
                0, "MEDIUM", f"Date column '{col}' not found in {fname}",
                f"Confirm '{col}' is included in the export"))
            continue
        parsed       = pd.to_datetime(df[col], errors="coerce")
        orig_nulls   = int(df[col].isna().sum())
        newly_bad    = int(parsed.isna().sum()) - orig_nulls
        if newly_bad > 0:
            results.append(make_result(cid, fname, "INVALID_DATE", "FAIL",
                newly_bad, "MEDIUM",
                f"'{col}' has {newly_bad:,} unparseable date values in {fname}",
                f"Standardise '{col}' to YYYY-MM-DD format at the source"))
        else:
            results.append(make_result(cid, fname, "INVALID_DATE", "PASS",
                0, "INFO", f"'{col}' -- all dates parsed successfully", "No action required"))
    return results


def check_non_numeric_amounts(
    df: pd.DataFrame, numeric_cols: list[str], fname: str, ctr: list
) -> list[dict]:
    """Flag rows where numeric fields contain non-numeric data.

    Business rationale: Non-numeric amounts silently become NaN in pandas,
    producing incorrect aggregations and blank cells in reports.
    """
    results = []
    for col in numeric_cols:
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns:
            results.append(make_result(cid, fname, "NON_NUMERIC_AMOUNT", "FAIL",
                0, "HIGH", f"Numeric column '{col}' not found in {fname}",
                f"Ensure '{col}' is exported from the source"))
            continue
        coerced = pd.to_numeric(df[col], errors="coerce")
        bad_cnt = int(coerced.isna().sum()) - int(df[col].isna().sum())
        if bad_cnt > 0:
            results.append(make_result(cid, fname, "NON_NUMERIC_AMOUNT", "FAIL",
                bad_cnt, "HIGH",
                f"'{col}' has {bad_cnt:,} non-numeric values in {fname}",
                f"Remove currency symbols, commas, or text from '{col}' before loading"))
        else:
            results.append(make_result(cid, fname, "NON_NUMERIC_AMOUNT", "PASS",
                0, "INFO", f"'{col}' -- all values are numeric", "No action required"))
    return results


def check_missing_account_ids(df: pd.DataFrame, fname: str, ctr: list) -> list[dict]:
    """Flag rows where account_id is null or zero.

    Business rationale: Unidentifiable accounts cannot be matched to a legal
    entity, making the transaction unauditable.
    """
    ctr[0] += 1
    cid = ctr[0]
    if "account_id" not in df.columns:
        return [make_result(cid, fname, "MISSING_ACCOUNT_ID", "PASS",
            0, "INFO", "account_id column not applicable for this file", "No action required")]

    null_count = int(df["account_id"].isna().sum())
    zero_count = int((pd.to_numeric(df["account_id"], errors="coerce") == 0).sum())
    total_bad  = null_count + zero_count

    if total_bad > 0:
        return [make_result(cid, fname, "MISSING_ACCOUNT_ID", "FAIL",
            total_bad, "HIGH",
            f"account_id is null or zero for {total_bad:,} rows in {fname}",
            "Ensure account_id is populated from source before export")]
    return [make_result(cid, fname, "MISSING_ACCOUNT_ID", "PASS",
        0, "INFO", "account_id -- no nulls or zero values found", "No action required")]


def check_invalid_statuses(
    df: pd.DataFrame, valid_statuses: dict, fname: str, ctr: list
) -> list[dict]:
    """Flag rows where a categorical status field contains an unexpected value.

    Business rationale: Unrecognised status codes are skipped by filter logic
    in dashboards, causing those records to appear as gaps in reporting.
    """
    results = []
    for col, valid_vals in valid_statuses.items():
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns or not valid_vals:
            results.append(make_result(cid, fname, "INVALID_STATUS_VALUE", "PASS",
                0, "INFO", f"'{col}' -- column not present or no valid list defined",
                "No action required"))
            continue
        invalid = (~df[col].str.upper().str.strip().isin([v.upper() for v in valid_vals])
                   & df[col].notna())
        bad_cnt = int(invalid.sum())
        if bad_cnt > 0:
            found = df.loc[invalid, col].unique()[:5].tolist()
            results.append(make_result(cid, fname, "INVALID_STATUS_VALUE", "FAIL",
                bad_cnt, "MEDIUM",
                (f"'{col}' has {bad_cnt:,} unexpected values in {fname}. "
                 f"Expected: {valid_vals}. Found (sample): {found}"),
                f"Standardise '{col}' values to the approved code list: {valid_vals}"))
        else:
            results.append(make_result(cid, fname, "INVALID_STATUS_VALUE", "PASS",
                0, "INFO", f"'{col}' -- all values are within approved list", "No action required"))
    return results


def check_duplicate_full_rows(df: pd.DataFrame, fname: str, ctr: list) -> list[dict]:
    """Flag fully duplicate rows (all columns identical).

    Business rationale: Exact row duplicates indicate a double-load from
    a source file, inflating record counts and financial totals.
    """
    ctr[0] += 1
    cid = ctr[0]
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        return [make_result(cid, fname, "DUPLICATE_FULL_ROW", "FAIL",
            dup_count, "MEDIUM",
            f"{dup_count:,} fully duplicate rows detected in {fname}",
            "Deduplicate before loading; investigate whether the file was loaded twice")]
    return [make_result(cid, fname, "DUPLICATE_FULL_ROW", "PASS",
        0, "INFO", "No fully duplicate rows found", "No action required")]


def check_critical_nulls(
    df: pd.DataFrame, critical_cols: list[str], fname: str, ctr: list
) -> list[dict]:
    """Flag null values in columns that must never be empty.

    Business rationale: These fields control routing, severity scoring, and
    ownership assignment.  A null renders the record operationally unusable.
    """
    results = []
    for col in critical_cols:
        ctr[0] += 1
        cid = ctr[0]
        if col not in df.columns:
            results.append(make_result(cid, fname, "NULL_CRITICAL_FIELD", "FAIL",
                0, "HIGH", f"Critical field '{col}' is absent from {fname}",
                f"Ensure '{col}' is present in the export"))
            continue
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            results.append(make_result(cid, fname, "NULL_CRITICAL_FIELD", "FAIL",
                null_count, "HIGH",
                f"Critical field '{col}' is null for {null_count:,} rows in {fname}",
                f"Populate '{col}' before loading -- this field is required for operational use"))
        else:
            results.append(make_result(cid, fname, "NULL_CRITICAL_FIELD", "PASS",
                0, "INFO", f"'{col}' -- no nulls found in critical field", "No action required"))
    return results


# ─────────────────────────────────────────────
# ORCHESTRATE CHECKS FOR A SINGLE FILE
# ─────────────────────────────────────────────

def run_all_checks_for_file(fname: str, config: dict, ctr: list) -> list[dict]:
    """Load a file and run all applicable quality checks."""
    path = DATA_DIR / fname
    df   = load_csv_safe(path)
    if df is None:
        ctr[0] += 1
        return [make_result(ctr[0], fname, "FILE_NOT_FOUND", "FAIL", 0, "HIGH",
            f"{fname} was not found in {DATA_DIR}",
            "Confirm the file path and re-run the pipeline export")]

    print(f"\n  Checking: {fname} ({len(df):,} rows) ...")
    results: list[dict] = []

    required_cols  = config.get("required_cols", [])
    id_cols        = config.get("id_cols", [])
    date_cols      = config.get("date_cols", [])
    numeric_cols   = config.get("numeric_cols", [])
    valid_statuses = config.get("valid_statuses", {})
    critical_nulls = config.get("critical_null_cols", [])

    results += check_missing_required_fields(df, required_cols, fname, ctr)
    results += check_duplicate_ids(df, id_cols, fname, ctr)
    results += check_invalid_dates(df, date_cols, fname, ctr)
    results += check_non_numeric_amounts(df, numeric_cols, fname, ctr)
    results += check_missing_account_ids(df, fname, ctr)
    results += check_invalid_statuses(df, valid_statuses, fname, ctr)
    results += check_duplicate_full_rows(df, fname, ctr)
    if critical_nulls:
        results += check_critical_nulls(df, critical_cols=critical_nulls, fname=fname, ctr=ctr)

    passed = sum(1 for r in results if r["check_status"] == "PASS")
    failed = sum(1 for r in results if r["check_status"] == "FAIL")
    print(f"    Checks run: {len(results)} | Passed: {passed} | Failed: {failed}")
    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("data_quality_checks.py -- Phase 8 Python Enhancement")
    print(f"Run date : {date.today()}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    # Use a mutable counter list so nested functions share the same counter
    ctr = [0]

    print("\nRunning data quality checks across all files ...")
    for fname, config in FILES_TO_CHECK.items():
        file_results = run_all_checks_for_file(fname, config, ctr)
        all_results += file_results

    # ── Assemble Output ───────────────────────
    df_out = pd.DataFrame(all_results)
    col_order = [
        "check_id", "input_file", "check_name", "check_status",
        "failed_record_count", "severity", "issue_description", "suggested_fix",
    ]
    for col in col_order:
        if col not in df_out.columns:
            df_out[col] = None
    df_out = df_out[col_order]

    out_path = OUTPUT_DIR / "data_quality_results.csv"
    df_out.to_csv(out_path, index=False)

    # ── Run Summary ───────────────────────────
    total_checks  = len(df_out)
    failed_checks = int((df_out["check_status"] == "FAIL").sum())
    passed_checks = total_checks - failed_checks
    pass_rate     = round(100 * passed_checks / total_checks, 1) if total_checks else 0

    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    print(f"  Files checked        : {len(FILES_TO_CHECK)}")
    print(f"  Total checks run     : {total_checks:,}")
    print(f"  Checks passed        : {passed_checks:,}")
    print(f"  Checks failed        : {failed_checks:,}")
    print(f"  Overall pass rate    : {pass_rate:.1f}%")
    if failed_checks > 0 and "severity" in df_out.columns:
        print("\n  Failed checks by severity:")
        failed_df = df_out[df_out["check_status"] == "FAIL"]
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            cnt = int((failed_df["severity"] == sev).sum())
            if cnt:
                print(f"    {sev:<8} : {cnt:,}")
    print(f"\n  Output written to    : {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
