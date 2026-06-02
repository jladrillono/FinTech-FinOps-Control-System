# Phase 8 -- Python Enhancement Layer
## Methodology Notes & Recruiter Reference

**Project:** FinTech Financial Operations Control & Reconciliation System  
**Phase:** 8 of 10 -- Python Enhancement and Automated Validation  
**Author:** Portfolio Project  
**Last Updated:** 2026-05-30  

---

## 1. Purpose of Phase 8

Phase 8 adds a Python-based validation and anomaly detection layer on top of the
SQL data model, Excel reporting model, and Power BI dashboards built in Phases 2-7.

The goal is **not** to build a generic machine learning model.  The goal is to
strengthen financial operations controls by catching data quality problems,
missing vendor files, unusual cash movements, and exception concentrations
**earlier in the process** -- before they surface as silent errors in reports.

This layer simulates how a FinOps analyst or data engineer would use Python to
automate the pre-flight checks that would otherwise be done manually in Excel.

---

## 2. Inputs Used

| File | Source | Records | Status |
|------|--------|---------|--------|
| `02_Data/custodian_balances.csv` | Phase 4 custodian simulation | 76,200 | Required |
| `02_Data/reconciliation_breaks.csv` | Phase 5 reconciliation | 5,582 | Required |
| `02_Data/exception_log.csv` | Phase 5 exception detection | 5,584 | Required |
| `02_Data/vendor_files.csv` | Phase 4 vendor simulation | 3,048 | Required |
| `02_Data/raw_stock_transactions.csv` | Phase 1 source data | 3,299 | Required |
| `02_Data/cash_transactions.csv` | Transaction-level cash data | N/A | Optional -- not present in current dataset |
| `02_Data/internal_ledger.csv` | Internal ledger balances | N/A | Optional -- not present in current dataset |

All monetary values in this project are treated as **simulated USD** values.

---

## 3. Scripts Created

### `anomaly_detection.py`
Detects unusual cash activity across custodian balances, reconciliation breaks,
and exception logs.  Uses **account-relative** statistical outlier detection
(z-score and IQR calculated within each account's history).  Also supports
optional `cash_transactions.csv` and `internal_ledger.csv` inputs if present.
Outputs both `anomaly_flags.csv` (detailed) and `anomaly_summary.csv` (dashboard-ready).

### `vendor_file_validation.py`
Validates vendor file delivery from `vendor_files.csv`.  Detects missing files,
late deliveries, duplicate file names, record count anomalies, invalid dates,
and failed validation statuses.  Derives file type consistently from file names
(e.g. `CUST_BAL`, `CUST_POS`) rather than using the generic `source_system` field.
Outputs `vendor_validation_results.csv`.

### `data_quality_checks.py`
Runs 76 reusable data quality checks across five Phase 3-7 CSV files.  Emits
one output row per check (PASS or FAIL) with severity, issue description, and
a suggested remediation action.  Outputs `data_quality_results.csv`.

### `run_all_validations.py`
Orchestrator that runs all three modules in sequence and produces the
consolidated `python_validation_summary.csv`.  Correctly separates anomaly flags
(informational) from deterministic validation failures in the summary.

---

## 4. Output Files Created

| Output File | Rows | Description |
|-------------|------|-------------|
| `06_Python/outputs/anomaly_flags.csv` | 55,788 | Detailed row-level anomaly flags with severity and review actions |
| `06_Python/outputs/anomaly_summary.csv` | 9 | Dashboard-ready summary -- one row per anomaly_type/severity |
| `06_Python/outputs/vendor_validation_results.csv` | 63 | Vendor file issues (missing, failed, low record count) |
| `06_Python/outputs/data_quality_results.csv` | 76 | One row per data quality check (PASS/FAIL) across 5 files |
| `06_Python/outputs/python_validation_summary.csv` | 3 | Rolled-up summary -- one row per validation module |

All outputs are clean CSVs with no index column, readable directly in Excel or
connectable to Power BI as flat-file data sources.

**Why two anomaly outputs?**  `anomaly_flags.csv` is the full audit trail --
every flagged balance, movement, and concentration.  `anomaly_summary.csv`
aggregates those flags into 9 compact rows that Power BI can use for KPI cards,
bar charts, and management review without cluttering visuals with row-level data.

---

## 5. Validation Checks Performed

### 5.1 Data Quality Checks (`data_quality_checks.py`)

| Check Name | Description |
|------------|-------------|
| `MISSING_COLUMN` | Required column absent from the file |
| `NULL_REQUIRED_FIELD` | Required column contains null values |
| `DUPLICATE_ID` | Primary key column contains duplicates |
| `INVALID_DATE` | Date column contains unparseable values |
| `NON_NUMERIC_AMOUNT` | Numeric column contains text or symbols |
| `MISSING_ACCOUNT_ID` | account_id is null or zero |
| `INVALID_STATUS_VALUE` | Categorical field contains unexpected values |
| `DUPLICATE_FULL_ROW` | All-column duplicates (potential double-load) |
| `NULL_CRITICAL_FIELD` | Fields required for routing/ownership are null |

**Result:** 76 checks run across 5 files | 70 passed | 6 failed | Pass rate: 92.1%

The 6 failures are all in `raw_stock_transactions.csv`, which is external data
with inconsistent column naming and format -- this is expected and documented.

### 5.2 Vendor File Validation Checks (`vendor_file_validation.py`)

| Check | Records Flagged | Severity |
|-------|----------------|----------|
| Missing files | 1 | HIGH |
| Late files | 0 | -- |
| Duplicate file names | 0 | -- |
| Duplicate date/file type | 0 | -- |
| Low record count | 61 | HIGH |
| Failed validation status | 1 | HIGH |

**File type derivation:** Each business date legitimately has two files
(`CUST_BAL` = cash balances, `CUST_POS` = security positions).  The file type
is derived from the file name prefix (e.g. `CUST_BAL_20220815.csv` -> `CUST_BAL`)
and used consistently across all validation outputs.

---

## 6. Anomaly Detection Logic (`anomaly_detection.py`)

### 6.1 Negative Cash Balances
- **Logic:** Flag any row where `custodian_cash_balance < 0`.
- **Severity:** MEDIUM (balance < 0) / HIGH (balance < -5,000 USD).
- **Rationale:** Negative balances may indicate overdrafts, missed funding
  entries, or erroneous custodian adjustments.
- **Result:** 49,872 flagged.  The high count reflects the simulation design where
  many accounts carry negative positions due to short sales and injected breaks.

### 6.2 Excess Cash Balances
- **Logic:** Flag balances > 25,000 USD.
- **Rationale:** Persistently high balances suggest uninvested cash, missed
  wire instructions, or incorrect postings.
- **Result:** 1,231 flagged.

### 6.3 Large Daily Cash Movements
- **Logic:** Calculate day-over-day balance change per account; flag if
  the absolute change exceeds 10,000 USD.
- **Rationale:** A very large intraday swing may indicate a duplicate wire,
  an erroneous journal, or a settlement failure.
- **Result:** 4 flagged.

### 6.4 Statistical Outliers (Account-Relative)
- **Z-score:** Calculated **within each account_id group**.  Accounts with
  fewer than 5 records or zero standard deviation are skipped.
- **IQR:** Q1, Q3, and Tukey fences are calculated **within each account_id
  group**.  Accounts with fewer than 5 records or zero IQR are skipped.
- **A record is flagged if either method fires.**
- **Rationale:** Each account has its own normal balance range.  A balance
  that is unusual relative to the same account's history is more meaningful than
  one that is unusual relative to the entire population.
- **Result:** 4,673 flagged as LOW severity (4,384 IQR + 289 z-score).

### 6.5 Break Concentration by Account and Category
- **Logic:** Identify the top-3 accounts by total dollar exposure and the
  top-3 break categories by frequency.
- **Rationale:** When a small number of accounts dominate break exposure,
  they represent elevated operational risk and should be prioritized.
- **Result:** 5 records flagged (3 accounts + 2 categories).

### 6.6 Exception Concentration by Root Cause
- **Logic:** Find the top-3 root causes among HIGH-severity exceptions.
- **Rationale:** Recurring HIGH exceptions with the same root cause indicate
  a systematic control gap, not a one-off data issue.
- **Result:** 3 records flagged (dominant root causes identified for escalation).

### 6.7 Optional: Large Cash Transactions
- **Logic:** If `cash_transactions.csv` exists, flag individual transactions
  where the absolute cash impact exceeds 10,000 USD.
- **Rationale:** Transaction-level detection catches large inflows/outflows
  that the daily balance movement check may mask if offsetting entries exist
  on the same day.
- **Current status:** File not present in the project dataset; check was skipped
  cleanly with an informational message.

### 6.8 Optional: Internal Ledger Anomalies
- **Logic:** If `internal_ledger.csv` exists, run negative balance, excess
  balance, and large daily movement checks mirroring the custodian checks.
- **Rationale:** Comparing internal ledger anomalies with custodian anomalies
  helps identify which side of the reconciliation is the source of breaks.
- **Current status:** File not present in the project dataset; checks were
  skipped cleanly with an informational message.

---

## 7. Thresholds Used and Why

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| Negative balance warn | < 0 USD | Any negative balance warrants investigation |
| Negative balance HIGH | < -5,000 USD | Exceeds typical fee/settlement variance; likely a funding error |
| Excess cash | > 25,000 USD | P75 of observed max + buffer; flags outlier high balances |
| Large daily movement | > 10,000 USD | Exceeds the 99th percentile of daily moves in the simulation |
| Z-score cutoff | > 3.0 std devs (per account) | Industry standard, applied within each account's balance history |
| IQR multiplier | 1.5x (per account) | Standard Tukey fence, applied within each account's balance history |
| Vendor lateness | > 4 hours after 06:00 | Allows for normal early-morning delivery variance |
| Min record count | < 10 | Indicates a clearly truncated or partial file |
| Max record count | > 1,500 | Exceeds maximum observed in this dataset; flags suspected duplicates |
| Top-N concentration | 3 | Focuses escalation on the most material risk concentrations |

All thresholds are documented in configuration sections at the top of each
script and can be adjusted without changing the business logic code.

---

## 8. Assumptions and Limitations

1. **Simulated data only.** All inputs are portfolio-project simulations using
   USD values.  Thresholds would need to be calibrated against actual trading
   volumes and custodian SLA agreements in a production environment.

2. **Negative balances are expected here.** In a real fund, negative balances
   would be far less common.  The high count (49,872) reflects the simulation
   design and injected exceptions.  In production, the threshold and business
   logic for negative balance treatment would be account-type-specific.

3. **High anomaly volume is a feature of the simulation, not a flaw.** The
   55,788 flags in `anomaly_flags.csv` are the detailed audit output.  The
   `anomaly_summary.csv` (9 rows) is the dashboard-ready layer that condenses
   this into actionable insight.  In production, negative balance flags would
   be filtered by account type, and suppression rules would reduce noise.

4. **Vendor file lateness cannot be fully tested** because the simulation
   assigns all files a receipt time of exactly 06:00, so no files appear late.
   The check logic is correct and would activate on real data with variable
   delivery times.

5. **Optional inputs (cash_transactions.csv, internal_ledger.csv) are not present.**
   The scripts attempt to load these files, skip cleanly when they are absent,
   and document the skip in the terminal output.  If these files are added in
   future phases, the checks will activate automatically.

6. **raw_stock_transactions.csv** is external data with inconsistent column
   naming.  The 6 quality check failures on this file are expected and
   documented.  The core financial data files all pass 100% of data quality checks.

7. **No machine learning is used.** Z-score and IQR are chosen because they
   are interpretable, explainable, and auditable -- qualities that matter in
   financial operations where every flag must be traceable to a business rule.

---

## 9. How Python Outputs Connect to the Broader Project

| Phase | Tool | Connection |
|-------|------|-----------|
| Phase 2-3 | SQL Server | Python reads CSV exports from SQL views; validation results can be loaded back to the `ctl` schema as a quality checkpoint |
| Phase 6 | Excel Model | All five CSV outputs are importable as flat-file data connections in Excel for inclusion in the Exception Dashboard and Control Matrix |
| Phase 7 | Power BI | `anomaly_summary.csv` is the recommended connection for KPI cards and bar charts; `anomaly_flags.csv` supports drill-through detail |
| Phase 5 | Exception Management | `anomaly_flags.csv` HIGH-severity rows can be cross-referenced with `exception_log.csv` to triage escalation priority |
| Phase 9 | Controls Documentation | Pass rates and check counts from `python_validation_summary.csv` can be incorporated into the Control Assessment Matrix as evidence of automated testing |

---

## 10. Interview-Ready Explanation

**"What did Python add to this project?"**

> Python added an automated validation and anomaly detection layer that runs
> before any reconciliation result is trusted.  Instead of manually reviewing
> each file, the scripts check for missing fields, duplicate IDs, unparseable
> dates, and invalid statuses across five source files in under 10 seconds.
>
> The anomaly detection script flags negative cash balances, excess cash,
> large daily movements, and statistical outliers using z-score and IQR
> methods -- all calculated **within each account's own history** so that the
> flags reflect genuinely unusual activity rather than normal cross-account
> differences.  The detailed output has 55,788 flags for audit purposes, but
> the dashboard-ready summary condenses this into 9 actionable rows that Power
> BI can display as KPI cards.
>
> The vendor file validation ensures custodian data actually arrived, on time,
> with the expected record count, before reconciliation begins.  File types are
> derived from file names -- `CUST_BAL` for cash balances, `CUST_POS` for
> positions -- and used consistently across all output rows.
>
> Together, the three scripts run 76 data quality checks, surface 55,788
> balance anomalies, and flag 63 vendor file issues -- providing a repeatable,
> auditable pre-flight check that complements the SQL logic, Excel model, and
> Power BI dashboard.  All outputs are clean CSVs with no index column, ready
> to plug directly into Excel or Power BI without additional transformation.

---

*This document is part of the FinTech Financial Operations Control & Reconciliation System portfolio project.  All values are simulated USD project values for portfolio demonstration purposes.*
