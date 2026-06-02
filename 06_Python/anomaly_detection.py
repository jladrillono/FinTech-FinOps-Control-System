"""
anomaly_detection.py
====================
Phase 8 -- Python Enhancement Layer
FinTech Financial Operations Control & Reconciliation System

Purpose:
    Detects unusual cash activity, negative/excess balances, large daily movements,
    statistical outliers (account-relative), and unusual exception concentrations.
    Outputs both detailed anomaly_flags.csv and dashboard-ready anomaly_summary.csv.

Business context:
    This script strengthens operational controls by surfacing anomalies that
    may indicate data-quality issues, reconciliation errors, or control
    breakdowns earlier in the review cycle.

Inputs (required):
    - 02_Data/custodian_balances.csv
    - 02_Data/reconciliation_breaks.csv
    - 02_Data/exception_log.csv

Inputs (optional -- used if present, skipped cleanly if absent):
    - 02_Data/cash_transactions.csv
    - 02_Data/internal_ledger.csv

Outputs:
    - 06_Python/outputs/anomaly_flags.csv       (detailed row-level flags)
    - 06_Python/outputs/anomaly_summary.csv      (dashboard-ready summary)
"""

import re
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "02_Data"
OUTPUT_DIR   = PROJECT_ROOT / "06_Python" / "outputs"

# Required source files
CUSTODIAN_BALANCES_FILE     = DATA_DIR / "custodian_balances.csv"
RECONCILIATION_BREAKS_FILE  = DATA_DIR / "reconciliation_breaks.csv"
EXCEPTION_LOG_FILE          = DATA_DIR / "exception_log.csv"

# Optional source files -- loaded if present, skipped if absent
CASH_TRANSACTIONS_FILE      = DATA_DIR / "cash_transactions.csv"
INTERNAL_LEDGER_FILE        = DATA_DIR / "internal_ledger.csv"

# Thresholds (documented rationale in Python_Notes.md)
NEGATIVE_BALANCE_WARN_THRESHOLD   = 0          # USD -- flag anything below 0
NEGATIVE_BALANCE_HIGH_THRESHOLD   = -5_000     # USD -- severe if < -5,000

EXCESS_CASH_THRESHOLD             = 25_000     # USD -- flags outlier high balances

LARGE_MOVEMENT_THRESHOLD          = 10_000     # USD -- exceeds typical daily swing

# Statistical outlier detection (calculated per account)
Z_SCORE_THRESHOLD                 = 3.0        # Balances > 3 std devs from account mean
IQR_MULTIPLIER                    = 1.5        # Standard Tukey fence per account

# Break concentration
CONCENTRATION_TOP_N               = 3          # Flag top-N concentrated accounts

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def load_csv(path: Path, required_cols: list[str]) -> pd.DataFrame | None:
    """Load a CSV with strict column validation.

    Returns None (and prints a clear error) if the file is missing or any
    required column is absent, preventing downstream KeyError failures.
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


def load_optional_csv(path: Path, required_cols: list[str]) -> pd.DataFrame | None:
    """Load an optional CSV -- returns None silently if file is absent.

    If the file exists but is missing required columns, prints a warning and
    returns None so the check is skipped cleanly.
    """
    if not path.exists():
        print(f"  [INFO] Optional file not found: {path.name} -- skipping related checks")
        return None

    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"  [WARN] {path.name} exists but is missing columns {missing} -- skipping")
        return None
    return df


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Coerce a column to numeric, replacing non-parseable values with NaN."""
    return pd.to_numeric(series, errors="coerce")


def safe_to_date(series: pd.Series) -> pd.Series:
    """Coerce a column to datetime, replacing unparseable values with NaT."""
    return pd.to_datetime(series, errors="coerce")


def build_anomaly_row(
    anomaly_type: str,
    severity: str,
    reason_code: str,
    review_action: str,
    source_file: str,
    account_id=None,
    transaction_id=None,
    transaction_date=None,
    amount=None,
    balance=None,
    threshold_value=None,
) -> dict:
    """Construct a single anomaly record (anomaly_id is assigned at the end)."""
    return {
        "account_id":       account_id,
        "transaction_id":   transaction_id,
        "transaction_date": transaction_date,
        "anomaly_type":     anomaly_type,
        "amount":           amount,
        "balance":          balance,
        "threshold_value":  threshold_value,
        "severity":         severity,
        "reason_code":      reason_code,
        "review_action":    review_action,
        "source_file":      source_file,
    }


def create_anomaly_summary(df_out: pd.DataFrame) -> pd.DataFrame:
    """Create a dashboard-ready summary aggregated by anomaly_type and severity.

    Business rationale: The detailed anomaly_flags.csv may contain tens of
    thousands of rows.  anomaly_summary.csv gives Power BI a compact, actionable
    dataset suitable for KPI cards, bar charts, and management review without
    cluttering visuals with row-level detail.
    """
    summary = (
        df_out.groupby(["anomaly_type", "severity"], dropna=False)
        .agg(
            record_count=("anomaly_id", "count"),
            unique_accounts=("account_id", "nunique"),
            total_amount=("amount", "sum"),
            avg_balance=("balance", "mean"),
        )
        .reset_index()
    )
    # Round numeric columns for readability
    summary["total_amount"] = summary["total_amount"].round(2)
    summary["avg_balance"]  = summary["avg_balance"].round(2)

    # Add recommended action per anomaly type
    action_map = {
        "NEGATIVE_CASH_BALANCE":            "Review funding, settlement timing, and injected breaks.",
        "EXCESS_CASH_BALANCE":              "Confirm whether idle cash or posting error exists.",
        "LARGE_DAILY_CASH_MOVEMENT":        "Review cash transactions supporting the movement.",
        "STATISTICAL_OUTLIER_Z_SCORE":      "Secondary review -- confirm balance is expected for this account.",
        "STATISTICAL_OUTLIER_IQR":          "Secondary review -- confirm balance is expected for this account.",
        "HIGH_BREAK_CONCENTRATION_ACCOUNT": "Prioritize reconciliation review for concentrated accounts.",
        "HIGH_BREAK_CONCENTRATION_CATEGORY":"Review systemic cause of dominant break category.",
        "HIGH_EXCEPTION_CONCENTRATION":     "Perform root-cause review for recurring HIGH exceptions.",
        "LARGE_CASH_TRANSACTION":           "Verify supporting documentation for large cash inflow/outflow.",
        "LEDGER_NEGATIVE_BALANCE":          "Investigate internal ledger funding or settlement entry.",
        "LEDGER_EXCESS_BALANCE":            "Confirm internal ledger balance is expected.",
        "LEDGER_LARGE_DAILY_MOVEMENT":      "Verify internal ledger movement against custodian balance.",
    }
    summary["recommended_action"] = (
        summary["anomaly_type"]
        .map(action_map)
        .fillna("Review supporting source records and related exceptions.")
    )
    return summary


# ─────────────────────────────────────────────
# ANOMALY CHECK FUNCTIONS
# ─────────────────────────────────────────────

def detect_negative_balances(df: pd.DataFrame) -> list[dict]:
    """Flag accounts with negative custodian cash balances.

    Business rationale: A negative balance may indicate an overdraft, a missed
    funding entry, or an erroneous custodian adjustment that needs investigation.
    """
    rows = []
    df = df.copy()
    df["custodian_cash_balance"] = safe_to_numeric(df["custodian_cash_balance"])
    df["balance_date"] = safe_to_date(df["balance_date"])

    negatives = df[df["custodian_cash_balance"] < NEGATIVE_BALANCE_WARN_THRESHOLD]

    for _, rec in negatives.iterrows():
        bal = rec["custodian_cash_balance"]
        severity = "HIGH" if bal < NEGATIVE_BALANCE_HIGH_THRESHOLD else "MEDIUM"
        rows.append(build_anomaly_row(
            anomaly_type="NEGATIVE_CASH_BALANCE",
            severity=severity,
            reason_code="BALANCE_BELOW_ZERO",
            review_action="Investigate funding entries and custodian adjustments",
            source_file="custodian_balances.csv",
            account_id=rec.get("account_id"),
            transaction_date=str(rec["balance_date"].date()) if pd.notna(rec["balance_date"]) else None,
            balance=round(bal, 2),
            threshold_value=NEGATIVE_BALANCE_WARN_THRESHOLD,
        ))
    print(f"  Negative balance records flagged: {len(rows)}")
    return rows


def detect_excess_cash(df: pd.DataFrame) -> list[dict]:
    """Flag accounts where the cash balance exceeds the excess-cash threshold.

    Business rationale: Persistently high balances may signal uninvested cash,
    missed wire instructions, or incorrect account postings.
    """
    rows = []
    df = df.copy()
    df["custodian_cash_balance"] = safe_to_numeric(df["custodian_cash_balance"])
    df["balance_date"] = safe_to_date(df["balance_date"])

    excess = df[df["custodian_cash_balance"] > EXCESS_CASH_THRESHOLD]

    for _, rec in excess.iterrows():
        bal = rec["custodian_cash_balance"]
        rows.append(build_anomaly_row(
            anomaly_type="EXCESS_CASH_BALANCE",
            severity="MEDIUM",
            reason_code="BALANCE_ABOVE_THRESHOLD",
            review_action="Confirm balance is expected; check for uninvested cash or posting errors",
            source_file="custodian_balances.csv",
            account_id=rec.get("account_id"),
            transaction_date=str(rec["balance_date"].date()) if pd.notna(rec["balance_date"]) else None,
            balance=round(bal, 2),
            threshold_value=EXCESS_CASH_THRESHOLD,
        ))
    print(f"  Excess cash records flagged: {len(rows)}")
    return rows


def detect_large_daily_movements(df: pd.DataFrame) -> list[dict]:
    """Flag accounts with a single-day net cash change exceeding the threshold.

    Business rationale: A very large intraday swing may indicate an erroneous
    journal, a duplicate funding wire, or a settlement failure.
    """
    rows = []
    df = df.copy()
    df["custodian_cash_balance"] = safe_to_numeric(df["custodian_cash_balance"])
    df["balance_date"] = safe_to_date(df["balance_date"])
    df = df.dropna(subset=["balance_date", "custodian_cash_balance", "account_id"])
    df = df.sort_values(["account_id", "balance_date"])

    df["prev_balance"] = df.groupby("account_id")["custodian_cash_balance"].shift(1)
    df["daily_change"] = (df["custodian_cash_balance"] - df["prev_balance"]).abs()

    large = df[df["daily_change"] > LARGE_MOVEMENT_THRESHOLD]

    for _, rec in large.iterrows():
        rows.append(build_anomaly_row(
            anomaly_type="LARGE_DAILY_CASH_MOVEMENT",
            severity="HIGH",
            reason_code="DAILY_CHANGE_EXCEEDS_THRESHOLD",
            review_action="Verify funding wires, settlement activity, and journal entries for this date",
            source_file="custodian_balances.csv",
            account_id=rec.get("account_id"),
            transaction_date=str(rec["balance_date"].date()) if pd.notna(rec["balance_date"]) else None,
            amount=round(rec["daily_change"], 2),
            balance=round(rec["custodian_cash_balance"], 2),
            threshold_value=LARGE_MOVEMENT_THRESHOLD,
        ))
    print(f"  Large daily movement records flagged: {len(rows)}")
    return rows


def detect_statistical_outliers(df: pd.DataFrame) -> list[dict]:
    """Flag balances that are statistical outliers within their own account.

    Business rationale: Each account has its own normal balance range.  A balance
    that is unusual relative to the same account's history is more meaningful than
    one that is unusual relative to the entire population.

    Implementation:
    - Z-score is calculated within each account_id group.
    - IQR fences are calculated within each account_id group.
    - Accounts with zero standard deviation or fewer than 5 records are skipped.
    """
    rows = []
    df = df.copy()
    df["custodian_cash_balance"] = safe_to_numeric(df["custodian_cash_balance"])
    df["balance_date"] = safe_to_date(df["balance_date"])
    df = df.dropna(subset=["custodian_cash_balance", "account_id"])

    # Account-relative z-score
    def account_z_score(x):
        std = x.std(ddof=0)
        if std == 0 or len(x) < 5:
            return pd.Series(0.0, index=x.index)
        return (x - x.mean()) / std

    df["z_score"] = df.groupby("account_id")["custodian_cash_balance"].transform(account_z_score)

    # Account-relative IQR
    def account_iqr_flag(x):
        if len(x) < 5:
            return pd.Series(False, index=x.index)
        q1 = x.quantile(0.25)
        q3 = x.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return pd.Series(False, index=x.index)
        lower = q1 - IQR_MULTIPLIER * iqr
        upper = q3 + IQR_MULTIPLIER * iqr
        return (x < lower) | (x > upper)

    df["iqr_outlier"] = df.groupby("account_id")["custodian_cash_balance"].transform(account_iqr_flag)

    outliers = df[
        (df["z_score"].abs() > Z_SCORE_THRESHOLD) |
        (df["iqr_outlier"] == True)
    ]

    for _, rec in outliers.iterrows():
        z = rec.get("z_score", 0.0)
        method = "Z_SCORE" if abs(z) > Z_SCORE_THRESHOLD else "IQR"
        rows.append(build_anomaly_row(
            anomaly_type=f"STATISTICAL_OUTLIER_{method}",
            severity="LOW",
            reason_code=f"BALANCE_IS_ACCOUNT_RELATIVE_OUTLIER_{method}",
            review_action="Secondary review -- confirm balance is operationally expected for this account",
            source_file="custodian_balances.csv",
            account_id=rec.get("account_id"),
            transaction_date=str(rec["balance_date"].date()) if pd.notna(rec.get("balance_date")) else None,
            balance=round(rec["custodian_cash_balance"], 2),
            threshold_value=round(float(Z_SCORE_THRESHOLD if method == "Z_SCORE" else IQR_MULTIPLIER), 2),
        ))
    print(f"  Statistical outlier records flagged: {len(rows)}")
    return rows


def detect_break_concentration(df_breaks: pd.DataFrame) -> list[dict]:
    """Flag accounts and root causes with disproportionate break concentration.

    Business rationale: When a small number of accounts or root causes account
    for the majority of break exposure, they represent elevated operational risk
    and should be prioritized in the reconciliation review.
    """
    rows = []
    df = df_breaks.copy()
    df["dollar_exposure"] = safe_to_numeric(df["dollar_exposure"])
    df["business_date"]   = safe_to_date(df["business_date"])
    df = df.dropna(subset=["dollar_exposure"])

    # Top-N accounts by total exposure
    account_exp = (
        df.groupby("account_id")["dollar_exposure"]
        .sum()
        .nlargest(CONCENTRATION_TOP_N)
    )
    for account_id, total_exp in account_exp.items():
        rows.append(build_anomaly_row(
            anomaly_type="HIGH_BREAK_CONCENTRATION_ACCOUNT",
            severity="HIGH",
            reason_code="TOP_N_ACCOUNT_EXPOSURE",
            review_action=f"Prioritize reconciliation review for account {account_id}",
            source_file="reconciliation_breaks.csv",
            account_id=account_id,
            amount=round(total_exp, 2),
            threshold_value=CONCENTRATION_TOP_N,
        ))

    # Top-N break categories by record count
    cat_counts = df["break_category"].value_counts().nlargest(CONCENTRATION_TOP_N)
    for cat, count in cat_counts.items():
        rows.append(build_anomaly_row(
            anomaly_type="HIGH_BREAK_CONCENTRATION_CATEGORY",
            severity="MEDIUM",
            reason_code="DOMINANT_BREAK_CATEGORY",
            review_action=f"Review systemic cause of frequent '{cat}' breaks",
            source_file="reconciliation_breaks.csv",
            threshold_value=CONCENTRATION_TOP_N,
            amount=float(count),
        ))

    print(f"  Break concentration records flagged: {len(rows)}")
    return rows


def detect_exception_concentration(df_exc: pd.DataFrame) -> list[dict]:
    """Flag root causes with disproportionate share of HIGH-severity exceptions.

    Business rationale: Recurring HIGH exceptions with the same root cause
    indicate a systematic control gap rather than a one-off data issue.
    """
    rows = []
    df = df_exc.copy()
    high = df[df["severity"] == "HIGH"]
    if high.empty:
        print("  No HIGH severity exceptions found.")
        return rows

    by_root = high.groupby("root_cause").size().nlargest(CONCENTRATION_TOP_N)
    for root_cause, count in by_root.items():
        rows.append(build_anomaly_row(
            anomaly_type="HIGH_EXCEPTION_CONCENTRATION",
            severity="HIGH",
            reason_code="RECURRING_HIGH_SEVERITY_ROOT_CAUSE",
            review_action=f"Perform root-cause review for '{root_cause}'; consider control enhancement",
            source_file="exception_log.csv",
            amount=float(count),
            threshold_value=CONCENTRATION_TOP_N,
        ))
    print(f"  Exception concentration records flagged: {len(rows)}")
    return rows


# ── OPTIONAL: Cash Transactions Checks ───────

def detect_large_cash_transactions(df_cash: pd.DataFrame) -> list[dict]:
    """Flag individual cash transactions that exceed the large-movement threshold.

    Business rationale: Transaction-level detection catches large inflows/outflows
    that the daily balance movement check may mask if offsetting entries exist
    on the same day.
    """
    rows = []
    df = df_cash.copy()

    # Identify the amount column -- common names in fintech datasets
    amount_col = None
    for candidate in ["cash_impact", "amount", "transaction_amount", "net_amount"]:
        if candidate in df.columns:
            amount_col = candidate
            break
    if amount_col is None:
        print("  [WARN] No recognizable amount column in cash_transactions.csv -- skipping")
        return rows

    df[amount_col] = safe_to_numeric(df[amount_col])
    large = df[df[amount_col].abs() > LARGE_MOVEMENT_THRESHOLD]

    date_col = None
    for candidate in ["transaction_date", "business_date", "trade_date", "date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    for _, rec in large.iterrows():
        txn_date = None
        if date_col and pd.notna(rec.get(date_col)):
            txn_date = str(pd.to_datetime(rec[date_col], errors="coerce").date()) if pd.notna(pd.to_datetime(rec.get(date_col), errors="coerce")) else None

        rows.append(build_anomaly_row(
            anomaly_type="LARGE_CASH_TRANSACTION",
            severity="HIGH",
            reason_code="TRANSACTION_EXCEEDS_THRESHOLD",
            review_action="Verify supporting documentation for large cash inflow/outflow",
            source_file="cash_transactions.csv",
            account_id=rec.get("account_id"),
            transaction_id=rec.get("transaction_id"),
            transaction_date=txn_date,
            amount=round(float(rec[amount_col]), 2),
            threshold_value=LARGE_MOVEMENT_THRESHOLD,
        ))
    print(f"  Large cash transaction records flagged: {len(rows)}")
    return rows


# ── OPTIONAL: Internal Ledger Checks ─────────

def detect_ledger_anomalies(df_ledger: pd.DataFrame) -> list[dict]:
    """Run negative-balance, excess-balance, and large-movement checks on the
    internal ledger, mirroring the custodian balance checks.

    Business rationale: Comparing internal ledger anomalies with custodian
    anomalies helps identify which side of the reconciliation is the source
    of breaks.
    """
    rows = []
    df = df_ledger.copy()

    # Identify the balance column
    bal_col = None
    for candidate in ["ending_cash_balance", "cash_balance", "ledger_balance", "balance"]:
        if candidate in df.columns:
            bal_col = candidate
            break
    if bal_col is None:
        print("  [WARN] No recognizable balance column in internal_ledger.csv -- skipping")
        return rows

    date_col = None
    for candidate in ["balance_date", "business_date", "date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    df[bal_col] = safe_to_numeric(df[bal_col])
    if date_col:
        df[date_col] = safe_to_date(df[date_col])

    # Negative balances
    negatives = df[df[bal_col] < NEGATIVE_BALANCE_WARN_THRESHOLD]
    for _, rec in negatives.iterrows():
        bal = rec[bal_col]
        severity = "HIGH" if bal < NEGATIVE_BALANCE_HIGH_THRESHOLD else "MEDIUM"
        txn_date = str(rec[date_col].date()) if date_col and pd.notna(rec.get(date_col)) else None
        rows.append(build_anomaly_row(
            anomaly_type="LEDGER_NEGATIVE_BALANCE",
            severity=severity,
            reason_code="LEDGER_BALANCE_BELOW_ZERO",
            review_action="Investigate internal ledger funding or settlement entry",
            source_file="internal_ledger.csv",
            account_id=rec.get("account_id"),
            transaction_date=txn_date,
            balance=round(bal, 2),
            threshold_value=NEGATIVE_BALANCE_WARN_THRESHOLD,
        ))

    # Excess balances
    excess = df[df[bal_col] > EXCESS_CASH_THRESHOLD]
    for _, rec in excess.iterrows():
        txn_date = str(rec[date_col].date()) if date_col and pd.notna(rec.get(date_col)) else None
        rows.append(build_anomaly_row(
            anomaly_type="LEDGER_EXCESS_BALANCE",
            severity="MEDIUM",
            reason_code="LEDGER_BALANCE_ABOVE_THRESHOLD",
            review_action="Confirm internal ledger balance is expected",
            source_file="internal_ledger.csv",
            account_id=rec.get("account_id"),
            transaction_date=txn_date,
            balance=round(rec[bal_col], 2),
            threshold_value=EXCESS_CASH_THRESHOLD,
        ))

    # Large daily movements
    if date_col and "account_id" in df.columns:
        df = df.dropna(subset=[bal_col, "account_id"])
        if date_col:
            df = df.sort_values(["account_id", date_col])
        df["prev_bal"] = df.groupby("account_id")[bal_col].shift(1)
        df["daily_chg"] = (df[bal_col] - df["prev_bal"]).abs()
        large = df[df["daily_chg"] > LARGE_MOVEMENT_THRESHOLD]
        for _, rec in large.iterrows():
            txn_date = str(rec[date_col].date()) if pd.notna(rec.get(date_col)) else None
            rows.append(build_anomaly_row(
                anomaly_type="LEDGER_LARGE_DAILY_MOVEMENT",
                severity="HIGH",
                reason_code="LEDGER_DAILY_CHANGE_EXCEEDS_THRESHOLD",
                review_action="Verify internal ledger movement against custodian balance",
                source_file="internal_ledger.csv",
                account_id=rec.get("account_id"),
                transaction_date=txn_date,
                amount=round(rec["daily_chg"], 2),
                balance=round(rec[bal_col], 2),
                threshold_value=LARGE_MOVEMENT_THRESHOLD,
            ))

    print(f"  Internal ledger anomaly records flagged: {len(rows)}")
    return rows


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("anomaly_detection.py -- Phase 8 Python Enhancement Layer")
    print(f"Run date : {date.today()}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_anomalies: list[dict] = []

    # ── Custodian Balances (required) ────────
    print("\n[1/5] Loading custodian_balances.csv ...")
    cb_required = ["account_id", "balance_date", "custodian_cash_balance"]
    df_cb = load_csv(CUSTODIAN_BALANCES_FILE, cb_required)

    if df_cb is not None:
        print("  Running: negative balance check ...")
        all_anomalies += detect_negative_balances(df_cb)

        print("  Running: excess cash check ...")
        all_anomalies += detect_excess_cash(df_cb)

        print("  Running: large daily movement check ...")
        all_anomalies += detect_large_daily_movements(df_cb)

        print("  Running: account-relative statistical outlier check ...")
        all_anomalies += detect_statistical_outliers(df_cb)

    # ── Reconciliation Breaks (required) ─────
    print("\n[2/5] Loading reconciliation_breaks.csv ...")
    rb_required = ["account_id", "business_date", "break_category", "dollar_exposure"]
    df_rb = load_csv(RECONCILIATION_BREAKS_FILE, rb_required)

    if df_rb is not None:
        print("  Running: break concentration check ...")
        all_anomalies += detect_break_concentration(df_rb)

    # ── Exception Log (required) ─────────────
    print("\n[3/5] Loading exception_log.csv ...")
    exc_required = ["severity", "root_cause", "account_id"]
    df_exc = load_csv(EXCEPTION_LOG_FILE, exc_required)

    if df_exc is not None:
        print("  Running: exception concentration check ...")
        all_anomalies += detect_exception_concentration(df_exc)

    # ── Cash Transactions (optional) ─────────
    print("\n[4/5] Loading cash_transactions.csv (optional) ...")
    cash_required = ["account_id"]  # Minimal; amount column auto-detected
    df_cash = load_optional_csv(CASH_TRANSACTIONS_FILE, cash_required)

    if df_cash is not None:
        print("  Running: large cash transaction check ...")
        all_anomalies += detect_large_cash_transactions(df_cash)

    # ── Internal Ledger (optional) ───────────
    print("\n[5/5] Loading internal_ledger.csv (optional) ...")
    ledger_required = ["account_id"]  # Minimal; balance column auto-detected
    df_ledger = load_optional_csv(INTERNAL_LEDGER_FILE, ledger_required)

    if df_ledger is not None:
        print("  Running: internal ledger anomaly checks ...")
        all_anomalies += detect_ledger_anomalies(df_ledger)

    # ── Assemble Output ──────────────────────
    if not all_anomalies:
        print("\n[RESULT] No anomalies detected.")
        return

    df_out = pd.DataFrame(all_anomalies)
    df_out["anomaly_id"] = range(1, len(df_out) + 1)

    output_cols = [
        "anomaly_id", "account_id", "transaction_id", "transaction_date",
        "anomaly_type", "amount", "balance", "threshold_value",
        "severity", "reason_code", "review_action", "source_file",
    ]
    for col in output_cols:
        if col not in df_out.columns:
            df_out[col] = None
    df_out = df_out[output_cols]

    # Write detailed anomaly flags
    flags_path = OUTPUT_DIR / "anomaly_flags.csv"
    df_out.to_csv(flags_path, index=False)

    # Write dashboard-ready anomaly summary
    df_summary = create_anomaly_summary(df_out)
    summary_path = OUTPUT_DIR / "anomaly_summary.csv"
    df_summary.to_csv(summary_path, index=False)

    # ── Run Summary ──────────────────────────
    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    print(f"  Total anomalies flagged  : {len(df_out):,}")
    print(f"  HIGH severity            : {(df_out['severity'] == 'HIGH').sum():,}")
    print(f"  MEDIUM severity          : {(df_out['severity'] == 'MEDIUM').sum():,}")
    print(f"  LOW severity             : {(df_out['severity'] == 'LOW').sum():,}")
    print(f"\n  Anomaly summary rows     : {len(df_summary):,}")
    print(f"\n  Detailed output          : {flags_path}")
    print(f"  Summary output           : {summary_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
