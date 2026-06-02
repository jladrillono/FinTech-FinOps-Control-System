"""
run_all_validations.py
======================
Phase 8 -- Python Enhancement Layer
FinTech Financial Operations Control & Reconciliation System

Purpose:
    Orchestrator script that runs all three Phase 8 validation modules and
    produces the consolidated python_validation_summary.csv.

    Execute this script to run the full Phase 8 validation suite in one step:
        python 06_Python/run_all_validations.py

Outputs:
    - 06_Python/outputs/anomaly_flags.csv
    - 06_Python/outputs/anomaly_summary.csv
    - 06_Python/outputs/vendor_validation_results.csv
    - 06_Python/outputs/data_quality_results.csv
    - 06_Python/outputs/python_validation_summary.csv
"""

import sys
import io
import importlib.util
import pandas as pd
from pathlib import Path
from datetime import date

# Ensure UTF-8 output on Windows terminals that default to cp1252
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR  = PROJECT_ROOT / "06_Python"
OUTPUT_DIR   = PROJECT_ROOT / "06_Python" / "outputs"

MODULE_META = {
    "anomaly_detection": {
        "output_file":  "anomaly_flags.csv",
        "input_files":  "custodian_balances.csv, reconciliation_breaks.csv, exception_log.csv (+ optional: cash_transactions.csv, internal_ledger.csv)",
        "checks":       "Negative balances, excess cash, large daily movements, account-relative statistical outliers, break/exception concentration, optional cash transaction and ledger checks",
    },
    "vendor_file_validation": {
        "output_file":  "vendor_validation_results.csv",
        "input_files":  "vendor_files.csv",
        "checks":       "Missing files, late files, duplicate files, record count anomalies, invalid dates, failed validation status",
    },
    "data_quality_checks": {
        "output_file":  "data_quality_results.csv",
        "input_files":  "custodian_balances.csv, reconciliation_breaks.csv, exception_log.csv, vendor_files.csv, raw_stock_transactions.csv",
        "checks":       "Missing fields, duplicate IDs, invalid dates, non-numeric amounts, missing account IDs, invalid statuses, critical nulls",
    },
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_module(module_name: str):
    """Dynamically load a sibling Python module from the 06_Python directory."""
    spec = importlib.util.spec_from_file_location(
        module_name, SCRIPTS_DIR / f"{module_name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_module(module_name: str) -> str:
    """Execute the main() function of a module; return 'PASSED' or 'FAILED'."""
    try:
        mod = load_module(module_name)
        mod.main()
        return "PASSED"
    except Exception as exc:
        print(f"  [ERROR] {module_name} raised an exception: {exc}")
        return "FAILED"


def build_summary_row(module_name: str, status: str) -> dict:
    """Read the output CSV for a module and build a summary row.

    Key design decision (Issue 5):
    - anomaly_detection produces FLAGS for review, not deterministic pass/fail checks.
      Its summary row reports anomaly_count and high_risk_count but does NOT
      treat anomalies as failed_checks.  pass_rate is left blank (None).
    - vendor_file_validation produces deterministic issue findings.
      failed_checks = number of issues; pass_rate is meaningful.
    - data_quality_checks produces PASS/FAIL rows per check.
      failed_checks = number of FAIL rows; pass_rate is meaningful.
    """
    meta    = MODULE_META[module_name]
    out_csv = OUTPUT_DIR / meta["output_file"]
    run_dt  = str(date.today())

    if not out_csv.exists() or status == "FAILED":
        return {
            "run_date":         run_dt,
            "input_file":       meta["input_files"],
            "records_tested":   0,
            "checks_performed": 0,
            "failed_checks":    0,
            "anomaly_count":    0,
            "high_risk_count":  0,
            "pass_rate":        None,
            "notes":            f"Module {module_name} failed to complete",
        }

    df = pd.read_csv(out_csv)

    if module_name == "anomaly_detection":
        # Anomaly flags are NOT failed validation checks.  They are flags for
        # operational review.  failed_checks = 0; pass_rate = N/A.
        total         = len(df)
        checks_run    = 8   # number of anomaly check functions available
        failed_checks = 0   # anomalies are not failures
        anomaly_count = total
        high_risk     = int((df["severity"] == "HIGH").sum()) if "severity" in df.columns else 0
        pass_rate     = None  # N/A for anomaly detection
        notes         = f"{total:,} anomaly flags generated for review; {high_risk:,} HIGH severity"

    elif module_name == "vendor_file_validation":
        total         = len(df)
        checks_run    = 6
        failed_checks = total
        anomaly_count = 0
        high_risk     = int((df["severity"] == "HIGH").sum()) if "severity" in df.columns else 0
        pass_rate     = 0.0 if total > 0 else 100.0
        notes         = f"{total} validation issues; {high_risk} HIGH severity"

    elif module_name == "data_quality_checks":
        total = len(df)
        if "check_status" in df.columns:
            failed_checks = int((df["check_status"] == "FAIL").sum())
            high_risk     = int(((df["check_status"] == "FAIL") & (df["severity"] == "HIGH")).sum()) if "severity" in df.columns else 0
        else:
            failed_checks = int((df["failed_record_count"] > 0).sum()) if "failed_record_count" in df.columns else 0
            high_risk     = int(((df["severity"] == "HIGH") & (df["failed_record_count"] > 0)).sum()) if "severity" in df.columns else 0
        checks_run    = total
        anomaly_count = 0
        pass_rate     = round(100 * (total - failed_checks) / max(total, 1), 1)
        notes         = f"{failed_checks} of {total} checks failed; {high_risk} HIGH severity failures"

    else:
        total = checks_run = failed_checks = anomaly_count = high_risk = 0
        pass_rate = 100.0
        notes = "Unknown module"

    return {
        "run_date":         run_dt,
        "input_file":       meta["input_files"],
        "records_tested":   total,
        "checks_performed": checks_run,
        "failed_checks":    failed_checks,
        "anomaly_count":    anomaly_count,
        "high_risk_count":  high_risk,
        "pass_rate":        pass_rate,
        "notes":            notes,
    }

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("run_all_validations.py -- Phase 8 Full Validation Suite")
    print(f"Run date : {date.today()}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    statuses: dict[str, str] = {}
    for module_name in MODULE_META:
        print(f"\n{'-' * 60}")
        print(f"Running module: {module_name}")
        print(f"{'-' * 60}")
        statuses[module_name] = run_module(module_name)

    # ── Build Validation Summary ──────────────
    print("\n" + "=" * 60)
    print("Building python_validation_summary.csv ...")
    summary_rows = []
    for module_name, status in statuses.items():
        row = build_summary_row(module_name, status)
        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    col_order = [
        "run_date", "input_file", "records_tested", "checks_performed",
        "failed_checks", "anomaly_count", "high_risk_count", "pass_rate", "notes",
    ]
    for col in col_order:
        if col not in df_summary.columns:
            df_summary[col] = None
    df_summary = df_summary[col_order]

    summary_path = OUTPUT_DIR / "python_validation_summary.csv"
    df_summary.to_csv(summary_path, index=False)

    # ── Final Report ──────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 8 VALIDATION COMPLETE")
    print("=" * 60)
    for module_name, status in statuses.items():
        icon = "[OK]" if status == "PASSED" else "[FAIL]"
        print(f"  {icon} {module_name:<35} {status}")

    print("\n  Output files:")
    for fname in [
        "anomaly_flags.csv",
        "anomaly_summary.csv",
        "vendor_validation_results.csv",
        "data_quality_results.csv",
        "python_validation_summary.csv",
    ]:
        path = OUTPUT_DIR / fname
        if path.exists():
            rows = len(pd.read_csv(path))
            print(f"    {fname:<45} {rows:,} rows")
        else:
            print(f"    {fname:<45} NOT CREATED")

    print(f"\n  All outputs written to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
