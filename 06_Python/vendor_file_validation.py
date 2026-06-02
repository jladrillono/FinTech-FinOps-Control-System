"""
vendor_file_validation.py
=========================
Phase 8 -- Python Enhancement Layer
FinTech Financial Operations Control & Reconciliation System

Purpose:
    Validates vendor file delivery using vendor_files.csv.  Detects missing
    files, late deliveries, duplicate file entries, record-count anomalies,
    invalid dates, and failed validation statuses.  Results are written to
    vendor_validation_results.csv.

Business context:
    Timely and complete vendor file delivery is a prerequisite for daily
    reconciliation.  A missing or late file blocks the downstream cash and
    position comparison, creating a control gap that this script makes visible.

Inputs:
    - 02_Data/vendor_files.csv

Outputs:
    - 06_Python/outputs/vendor_validation_results.csv
"""

import re
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PROJECT_ROOT   = Path(__file__).resolve().parent.parent
DATA_DIR       = PROJECT_ROOT / "02_Data"
OUTPUT_DIR     = PROJECT_ROOT / "06_Python" / "outputs"

VENDOR_FILE    = DATA_DIR / "vendor_files.csv"

# Thresholds (documented rationale in Python_Notes.md)
LATENESS_HOURS   = 4       # Files expected by 06:00; tolerance = 4 hrs
MIN_RECORD_COUNT = 10      # Below this is suspiciously low
MAX_RECORD_COUNT = 1_500   # Above this is suspiciously high

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def load_csv(path: Path, required_cols: list[str]) -> pd.DataFrame | None:
    """Load CSV with strict column validation.

    Returns None if the file is missing or required columns are absent,
    preventing downstream KeyError failures.
    """
    if not path.exists():
        print(f"  [SKIP] File not found: {path.name}")
        return None

    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"  [ERROR] {path.name} is missing required columns: {missing}")
        return None
    return df


def extract_file_type(fname: str) -> str:
    """Derive a consistent file type from the vendor file name.

    Examples:
        CUST_BAL_20220815.csv  ->  CUST_BAL
        CUST_POS_20220815.csv  ->  CUST_POS
    """
    if not isinstance(fname, str):
        return "UNKNOWN"
    m = re.match(r"^(.+?)_(\d{8})", fname)
    return m.group(1) if m else fname.split(".")[0]


def make_result(
    validation_id,
    file_date,
    file_type: str,
    expected_status: str,
    actual_status: str,
    record_count,
    issue_type: str,
    severity: str,
    owner: str,
    review_action: str,
) -> dict:
    """Build a single validation result row."""
    return {
        "validation_id":   validation_id,
        "file_date":       file_date,
        "file_type":       file_type,
        "expected_status": expected_status,
        "actual_status":   actual_status,
        "record_count":    record_count,
        "issue_type":      issue_type,
        "severity":        severity,
        "owner":           owner,
        "review_action":   review_action,
    }


# ─────────────────────────────────────────────
# VALIDATION CHECK FUNCTIONS
#
# Every check function receives a DataFrame that already has
# the 'file_type_derived' column attached.  All output rows
# use file_type_derived (e.g. CUST_BAL, CUST_POS) instead of
# the generic source_system value.
# ─────────────────────────────────────────────

def check_missing_files(df: pd.DataFrame) -> list[dict]:
    """Flag rows where receipt_status indicates the file was not received."""
    rows = []
    missing = df[df["receipt_status"].str.upper().str.strip() == "MISSING"]
    for _, rec in missing.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status="RECEIVED",
            actual_status="MISSING",
            record_count=rec.get("record_count"),
            issue_type="MISSING_FILE",
            severity="HIGH",
            owner="Custodian Operations",
            review_action="Chase custodian for re-delivery; hold reconciliation for affected date",
        ))
    print(f"  Missing files flagged: {len(rows)}")
    return rows


def check_late_files(df: pd.DataFrame) -> list[dict]:
    """Flag files received after the expected delivery deadline."""
    rows = []
    df = df.copy()
    df["expected_date_parsed"]      = pd.to_datetime(df["expected_date"], errors="coerce")
    df["received_timestamp_parsed"] = pd.to_datetime(df["received_timestamp"], errors="coerce")

    valid = df.dropna(subset=["expected_date_parsed", "received_timestamp_parsed"])
    deadline_offset = timedelta(hours=6 + LATENESS_HOURS)
    valid = valid.copy()
    valid["deadline"] = valid["expected_date_parsed"] + deadline_offset
    late = valid[valid["received_timestamp_parsed"] > valid["deadline"]]

    for _, rec in late.iterrows():
        delay_hrs = (rec["received_timestamp_parsed"] - rec["deadline"]).total_seconds() / 3600
        rows.append(make_result(
            validation_id=None,
            file_date=str(rec["expected_date_parsed"].date()),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status="ON_TIME",
            actual_status="LATE",
            record_count=rec.get("record_count"),
            issue_type="LATE_FILE",
            severity="MEDIUM",
            owner="Custodian Operations",
            review_action=f"File received ~{delay_hrs:.1f}h after deadline; review SLA; investigate delay",
        ))
    print(f"  Late files flagged: {len(rows)}")
    return rows


def check_duplicate_files(df: pd.DataFrame) -> list[dict]:
    """Flag duplicate file names or same file type received twice for the same date.

    Note: The vendor_files dataset contains TWO file types per date by design
    (CUST_BAL = cash balances; CUST_POS = security positions).  The check groups
    by expected_date + file_type_derived so legitimate pairs are not flagged.
    """
    rows = []

    # Duplicate file names
    dup_names = df[df.duplicated(subset=["file_name"], keep=False)]
    if not dup_names.empty:
        for fname_val, grp in dup_names.groupby("file_name"):
            rows.append(make_result(
                validation_id=None,
                file_date=grp["expected_date"].iloc[0] if "expected_date" in grp.columns else None,
                file_type=grp["file_type_derived"].iloc[0],
                expected_status="UNIQUE",
                actual_status="DUPLICATE",
                record_count=grp["record_count"].iloc[0] if "record_count" in grp.columns else None,
                issue_type="DUPLICATE_FILE_NAME",
                severity="HIGH",
                owner="Reconciliation Team",
                review_action=f"Deduplicate '{fname_val}'; investigate why multiple copies were received",
            ))

    # Same file type received twice for same expected_date
    if "expected_date" in df.columns:
        dup_date_type = df[df.duplicated(subset=["expected_date", "file_type_derived"], keep=False)]
        if not dup_date_type.empty:
            for (edate, ftype), grp in dup_date_type.groupby(["expected_date", "file_type_derived"]):
                if grp["file_name"].nunique() > 1:
                    rows.append(make_result(
                        validation_id=None,
                        file_date=edate,
                        file_type=ftype,
                        expected_status="ONE_FILE_PER_TYPE_PER_DAY",
                        actual_status="MULTIPLE_FILES",
                        record_count=grp["record_count"].sum() if "record_count" in grp.columns else None,
                        issue_type="DUPLICATE_DATE_FILE_TYPE",
                        severity="MEDIUM",
                        owner="Reconciliation Team",
                        review_action="Confirm which file is authoritative; remove the duplicate before reconciliation",
                    ))
    print(f"  Duplicate file records flagged: {len(rows)}")
    return rows


def check_record_count_anomalies(df: pd.DataFrame) -> list[dict]:
    """Flag files where the record count falls outside expected bounds."""
    rows = []
    df = df.copy()
    df["record_count"] = pd.to_numeric(df["record_count"], errors="coerce")
    df_valid = df.dropna(subset=["record_count"])

    low  = df_valid[df_valid["record_count"] < MIN_RECORD_COUNT]
    high = df_valid[df_valid["record_count"] > MAX_RECORD_COUNT]

    for _, rec in low.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status=f">= {MIN_RECORD_COUNT} records",
            actual_status=f"{int(rec['record_count'])} records",
            record_count=rec["record_count"],
            issue_type="LOW_RECORD_COUNT",
            severity="HIGH",
            owner="Custodian Operations",
            review_action="Confirm file is complete; request re-delivery if truncated",
        ))

    for _, rec in high.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status=f"<= {MAX_RECORD_COUNT} records",
            actual_status=f"{int(rec['record_count'])} records",
            record_count=rec["record_count"],
            issue_type="HIGH_RECORD_COUNT",
            severity="MEDIUM",
            owner="Reconciliation Team",
            review_action="Verify no duplicate records were included in this file",
        ))
    print(f"  Record count anomaly records flagged: {len(rows)}")
    return rows


def check_invalid_dates(df: pd.DataFrame) -> list[dict]:
    """Flag rows where expected_date or received_timestamp cannot be parsed."""
    rows = []
    df = df.copy()
    df["expected_date_parsed"]      = pd.to_datetime(df.get("expected_date"),    errors="coerce")
    df["received_timestamp_parsed"] = pd.to_datetime(df.get("received_timestamp"), errors="coerce")

    bad_expected = df[df["expected_date_parsed"].isna()]
    bad_received = df[df["received_timestamp_parsed"].isna() & (df.get("receipt_status", "RECEIVED") != "MISSING")]

    for _, rec in bad_expected.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status="VALID_DATE",
            actual_status="INVALID_EXPECTED_DATE",
            record_count=rec.get("record_count"),
            issue_type="INVALID_DATE",
            severity="HIGH",
            owner="Reconciliation Team",
            review_action="Correct the expected_date field in the vendor file registry",
        ))

    for _, rec in bad_received.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status="VALID_TIMESTAMP",
            actual_status="INVALID_RECEIVED_TIMESTAMP",
            record_count=rec.get("record_count"),
            issue_type="INVALID_DATE",
            severity="MEDIUM",
            owner="Reconciliation Team",
            review_action="Correct the received_timestamp field in the vendor file registry",
        ))
    print(f"  Invalid date records flagged: {len(rows)}")
    return rows


def check_failed_validation_status(df: pd.DataFrame) -> list[dict]:
    """Flag files where the validation_status column shows FAILED."""
    rows = []
    failed = df[df["validation_status"].str.upper().str.strip() == "FAILED"]
    for _, rec in failed.iterrows():
        rows.append(make_result(
            validation_id=None,
            file_date=rec.get("expected_date"),
            file_type=rec.get("file_type_derived", "UNKNOWN"),
            expected_status="VALIDATED",
            actual_status="FAILED",
            record_count=rec.get("record_count"),
            issue_type="FAILED_VALIDATION_STATUS",
            severity="HIGH",
            owner="Reconciliation Team",
            review_action="Do not use this file in reconciliation; request corrected file from custodian",
        ))
    print(f"  Failed validation status records flagged: {len(rows)}")
    return rows


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("vendor_file_validation.py -- Phase 8 Python Enhancement")
    print(f"Run date : {date.today()}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    required_cols = [
        "source_file_id", "file_name", "source_system", "receipt_status",
        "record_count", "expected_date", "received_timestamp", "validation_status",
    ]
    print(f"\nLoading: {VENDOR_FILE.name} ...")
    df = load_csv(VENDOR_FILE, required_cols)

    if df is None:
        print("[ERROR] Cannot proceed without vendor_files.csv. Exiting.")
        return

    # Derive file_type_derived once and use it consistently in all checks
    df["file_type_derived"] = df["file_name"].apply(extract_file_type)
    print(f"  Rows loaded: {len(df):,}")
    print(f"  File types detected: {df['file_type_derived'].unique().tolist()}")

    all_results: list[dict] = []

    print("\nRunning validation checks ...")
    all_results += check_missing_files(df)
    all_results += check_late_files(df)
    all_results += check_duplicate_files(df)
    all_results += check_record_count_anomalies(df)
    all_results += check_invalid_dates(df)
    all_results += check_failed_validation_status(df)

    if not all_results:
        empty_cols = [
            "validation_id","file_date","file_type","expected_status",
            "actual_status","record_count","issue_type","severity","owner","review_action",
        ]
        df_out = pd.DataFrame(columns=empty_cols)
        print("\n[RESULT] No validation issues detected -- all files passed.")
    else:
        df_out = pd.DataFrame(all_results)
        df_out["validation_id"] = range(1, len(df_out) + 1)

        col_order = [
            "validation_id","file_date","file_type","expected_status",
            "actual_status","record_count","issue_type","severity","owner","review_action",
        ]
        for col in col_order:
            if col not in df_out.columns:
                df_out[col] = None
        df_out = df_out[col_order]

    out_path = OUTPUT_DIR / "vendor_validation_results.csv"
    df_out.to_csv(out_path, index=False)

    # ── Run Summary ──────────────────────────
    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    print(f"  Total issues flagged : {len(df_out):,}")
    if not df_out.empty and "severity" in df_out.columns:
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            count = (df_out["severity"] == sev).sum()
            if count:
                print(f"  {sev:<8} severity : {count:,}")
        if "issue_type" in df_out.columns:
            print(f"\n  Issues by type:")
            for itype, cnt in df_out["issue_type"].value_counts().items():
                print(f"    {itype:<35} {cnt:,}")
    print(f"\n  Output written to    : {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
