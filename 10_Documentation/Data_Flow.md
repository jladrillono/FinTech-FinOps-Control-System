# Data Flow

## Project Title

**FinTech Financial Operations Control & Reconciliation System**

## Purpose

This document explains how data moves through the FinTech Financial Operations Control & Reconciliation System from raw brokerage-style transactions to SQL transformations, ledger and position outputs, custodian simulation, reconciliation breaks, Excel review, Power BI reporting, Python validation, and control documentation.

The goal of the data flow is to show that each project output is traceable, reproducible, and connected to the broader financial operations workflow.

---

## 1. High-Level Data Flow

```text
Raw Transaction Data
        |
        v
SQL Raw Layer
        |
        v
SQL Staging Layer
        |
        v
SQL Core Financial Operations Tables
        |
        +-----------------------------+
        |                             |
        v                             v
Internal Ledger Balances       Security Positions
        |                             |
        +-------------+---------------+
                      |
                      v
Simulated Custodian Records
                      |
                      v
Reconciliation and Exception Detection
                      |
        +-------------+--------------+----------------+
        |                            |                |
        v                            v                v
Excel Review Model           Power BI Dashboard     Python Validation Outputs
        |                            |                |
        +-------------+--------------+----------------+
                      |
                      v
Control Documentation and Portfolio Reporting
```

---

## 2. Source Data Layer

## Input Files

The project begins with source and support files such as:

- `raw_stock_transactions.csv`
- `transaction_type_mapping.csv`
- `data_dictionary.csv`
- `custodian_balances.csv`
- `custodian_positions.csv`
- `reconciliation_breaks.csv`
- `exception_log.csv`
- `vendor_files.csv`
- `exception_injection_log.csv`
- Python output CSV files

## Business Purpose

The source data represents the raw operating activity and supporting evidence used to simulate a fintech financial operations workflow.

The main source file, `raw_stock_transactions.csv`, provides transaction-level activity such as deposits, withdrawals, dividends, market buys, market sells, fees, taxes, tickers, share quantities, prices, and transaction totals.

---

## 3. SQL Raw Layer

## Main Object

- `raw.raw_stock_transactions`

## Purpose

The raw layer preserves original source transaction records with minimal transformation. This allows later outputs to be traced back to the original imported records.

## Data Flow

```text
raw_stock_transactions.csv
        |
        v
raw.raw_stock_transactions
```

## Control Purpose

The raw layer supports:

- Source record preservation
- Import review
- Row count validation
- Duplicate checks
- Source-to-staging traceability
- Data quality review

---

## 4. SQL Staging Layer

## Main Objects

- `stg.transaction_type_mapping`
- `stg.vw_stock_transactions_clean`

## Purpose

The staging layer standardizes raw transaction fields and prepares records for core financial operations tables.

## Data Flow

```text
raw.raw_stock_transactions
        |
        v
stg.vw_stock_transactions_clean
        |
        v
Cleaned and typed transaction records
```

## Key Transformations

The staging layer supports:

- Date standardization
- Numeric conversion
- Text trimming
- Ticker standardization
- Transaction category mapping
- Cash impact preparation
- Security impact preparation
- Validation flag creation
- Identification of missing or invalid fields

## Control Purpose

The staging layer helps prevent bad source data from flowing silently into financial operations outputs.

---

## 5. SQL Core Layer

## Main Objects

- `core.customers`
- `core.accounts`
- `core.securities`
- `core.cash_transactions`
- `core.security_transactions`
- `core.internal_ledger_balances`
- `core.positions`
- `core.custodian_balances`
- `core.custodian_positions`
- `core.reconciliation_breaks`
- `core.exception_log`

## Purpose

The core layer stores business-ready financial operations data. This layer separates operational entities such as customers, accounts, securities, transactions, balances, positions, reconciliation breaks, and exceptions.

## Data Flow

```text
stg.vw_stock_transactions_clean
        |
        +--------------------------+
        |                          |
        v                          v
core.cash_transactions       core.security_transactions
        |                          |
        v                          v
core.internal_ledger_balances core.positions
```

## Business Purpose

The core layer supports:

- Cash activity review
- Security activity review
- Account-level cash balances
- Ticker-level security positions
- Custodian comparison
- Reconciliation break detection
- Exception tracking
- Excel and Power BI consumption

---

## 6. Ledger and Position Data Flow

## Cash Ledger Flow

```text
core.cash_transactions
        |
        v
Daily cash activity aggregation
        |
        v
core.internal_ledger_balances
```

## Cash Logic

```text
Beginning Cash Balance
+ Deposits
+ Dividends
+ Sale Proceeds
- Withdrawals
- Buy Costs
- Fees
- Taxes
= Ending Cash Balance
```

## Security Position Flow

```text
core.security_transactions
        |
        v
Daily share movement aggregation
        |
        v
core.positions
```

## Position Logic

```text
Beginning Shares
+ Shares Purchased
- Shares Sold
= Ending Shares
```

## Control Purpose

Ledger and position outputs become the internal records that will later be compared against custodian records.

---

## 7. Custodian Simulation Flow

## Main Objects

- `core.custodian_balances`
- `core.custodian_positions`
- `ctl.vendor_files`
- `ctl.exception_injection_log`

## Purpose

Custodian records simulate external vendor or custodian data used for reconciliation testing.

## Data Flow

```text
core.internal_ledger_balances       core.positions
        |                                  |
        v                                  v
core.custodian_balances            core.custodian_positions
        |                                  |
        +---------------+------------------+
                        |
                        v
ctl.exception_injection_log
```

## Controlled Exceptions

Controlled exceptions are injected to test the reconciliation process. Examples include:

- Cash balance differences
- Share quantity mismatches
- Missing records
- Duplicate records
- Timing differences
- Fee mismatches
- Dividend mismatches
- Missing or late vendor files

## Control Purpose

The simulation allows the project to prove whether known exceptions can be detected, classified, and reported.

---

## 8. Reconciliation and Exception Flow

## Main Objects and Views

- `core.reconciliation_breaks`
- `core.exception_log`
- `core.vw_daily_cash_reconciliation`
- `core.vw_security_position_reconciliation`
- `core.vw_transaction_match_reconciliation`
- `rpt.vw_reconciliation_summary`
- `rpt.vw_exception_summary`

## Purpose

The reconciliation layer compares internal records against simulated custodian records and creates operational exception outputs.

## Data Flow

```text
core.internal_ledger_balances       core.custodian_balances
        |                                  |
        +---------------+------------------+
                        |
                        v
core.vw_daily_cash_reconciliation
                        |
                        v
core.reconciliation_breaks
                        |
                        v
core.exception_log
```

```text
core.positions                       core.custodian_positions
        |                                  |
        +---------------+------------------+
                        |
                        v
core.vw_security_position_reconciliation
                        |
                        v
core.reconciliation_breaks
                        |
                        v
core.exception_log
```

## Break Types

The reconciliation process supports:

- Cash balance breaks
- Share quantity breaks
- Missing in custodian
- Missing in internal records
- Duplicate transactions
- Timing differences
- Value mismatches
- Unusual balance flags

## Exception Fields

The exception log includes:

- Root cause
- Owner
- Status
- SLA status
- Aging days
- Severity
- Dollar exposure
- Resolution notes
- Evidence file

## Control Purpose

This layer turns raw differences into reviewable operational exceptions.

---

## 9. SQL Reporting Layer

## Main Views

- `rpt.vw_cash_activity`
- `rpt.vw_security_activity`
- `rpt.vw_exception_summary`
- `rpt.vw_reconciliation_summary`
- `core.vw_daily_cash_reconciliation`
- `core.vw_security_position_reconciliation`
- `core.vw_transaction_match_reconciliation`
- `stg.vw_stock_transactions_clean`

## Purpose

The reporting layer provides cleaner, stable outputs for Excel, Power BI, Python validation, and portfolio evidence exports.

## Data Flow

```text
SQL Core Tables
        |
        v
SQL Reporting Views
        |
        +------------------+------------------+------------------+
        |                  |                  |
        v                  v                  v
Excel Model          Power BI Dashboard      SQL Evidence Exports
```

## Control Purpose

Reporting views reduce the need for downstream tools to query raw or overly complex tables directly.

---

## 10. Excel Model Data Flow

## Main File

- `FinOps_Reconciliation_Model.xlsx`

## Purpose

Excel acts as the manual review and tie-out layer.

## Data Flow

```text
SQL Outputs and CSV Exports
        |
        v
Excel Input Tabs
        |
        v
Excel Calculation and Review Tabs
        |
        v
Excel Dashboard, Tie-Outs, Exception Aging, Control Summary
```

## Excel Review Areas

The workbook supports:

- Reconciliation review
- Exception aging
- SLA status review
- Control summaries
- Tie-out checks
- Injection validation
- Ledger validation
- Manual review evidence

## Control Purpose

Excel provides transparent review evidence that connects SQL outputs to management reporting.

---

## 11. Power BI Dashboard Data Flow

## Main File

- `Dashboard.pbix`

## Purpose

Power BI converts operational outputs into executive-level reporting.

## Data Flow

```text
SQL / CSV / Excel Outputs
        |
        v
Power BI Data Model
        |
        v
DAX Measures
        |
        v
Dashboard Pages
```

## Dashboard Pages

1. Executive Overview
2. Cash Monitoring
3. Security Reconciliation
4. Exception Management
5. Controls
6. Validation
7. Python Validation & Anomaly Monitoring

## Dashboard Outputs

Power BI reports:

- Transaction volume
- Accounts reviewed
- Reconciliation breaks
- Open exceptions
- Over-SLA exceptions
- Dollar exposure
- Cash anomalies
- Security mismatches
- Root causes
- Owner workload
- Control performance
- Data quality results
- Vendor validation results
- Python anomaly outputs

## Control Purpose

Power BI gives management a consolidated view of operational risk and control performance.

---

## 12. Python Validation Data Flow

## Main Output Files

- `anomaly_flags.csv`
- `anomaly_summary.csv`
- `data_quality_results.csv`
- `python_validation_summary.csv`
- `vendor_validation_results.csv`

## Purpose

Python adds automated validation and anomaly monitoring.

## Data Flow

```text
SQL / CSV / Excel Outputs
        |
        v
Python Validation Scripts
        |
        v
Python Output CSV Files
        |
        +------------------+------------------+
        |                  |
        v                  v
Power BI Dashboard      Excel / Portfolio Evidence
```

## Python Validation Areas

Python checks:

- Missing required fields
- Duplicate records
- Invalid dates
- Nonnumeric amounts
- Negative cash balances
- Excess cash balances
- Large cash movements
- IQR outliers
- Z-score outliers
- Vendor file issues
- High break concentration
- High exception concentration

## Control Purpose

Python strengthens the control environment by creating repeatable anomaly and data quality checks.

---

## 13. Control Documentation Flow

## Main Outputs

- Control matrix
- Books-and-records index
- Evidence index
- Procedure document
- Monthly FinOps summary
- README
- Methodology
- Data flow documentation

## Data Flow

```text
SQL Outputs
Excel Outputs
Power BI Screenshots
Python Outputs
        |
        v
Control Matrix and Evidence Index
        |
        v
Executive Summary and Portfolio Documentation
```

## Control Purpose

Control documentation connects project outputs to business risks, control activities, evidence, owners, review frequency, and management communication.

---

## 14. Final Portfolio Data Flow

```text
Source Data
   |
   v
SQL Raw and Staging Layers
   |
   v
SQL Core Financial Operations Tables
   |
   v
Ledger, Positions, Custodian Simulation, Reconciliation, Exceptions
   |
   +--------------------+--------------------+--------------------+
   |                    |                    |
   v                    v                    v
Excel Model        Power BI Dashboard    Python Validation
   |                    |                    |
   +--------------------+--------------------+
                        |
                        v
Controls, Documentation, README, Screenshots, Portfolio Summary
```

---

## 15. Data Lineage Summary

| Output | Primary Source | Downstream Use |
|---|---|---|
| `core.cash_transactions` | Cleaned transactions | Cash ledger, Excel, Power BI |
| `core.security_transactions` | Cleaned transactions | Security positions, Excel, Power BI |
| `core.internal_ledger_balances` | Cash transactions | Custodian comparison, reconciliation |
| `core.positions` | Security transactions | Custodian comparison, reconciliation |
| `core.custodian_balances` | Internal ledger simulation | Cash reconciliation |
| `core.custodian_positions` | Position simulation | Security reconciliation |
| `core.reconciliation_breaks` | Internal vs custodian comparison | Exception log, Excel, Power BI |
| `core.exception_log` | Reconciliation breaks | Exception management, SLA aging, dashboard |
| `ctl.vendor_files` | Simulated vendor receipt records | File validation, Python, controls |
| `ctl.exception_injection_log` | Controlled exception design | Injection validation |
| Python output CSVs | SQL / CSV outputs | Anomaly monitoring, dashboard, evidence |
| Excel model | SQL / CSV outputs | Manual review and tie-outs |
| Power BI dashboard | SQL / Excel / CSV outputs | Management reporting |
| Control documentation | SQL, Excel, Power BI, Python evidence | Audit-ready project package |

---

## 16. Validation Points in the Data Flow

Validation is applied at multiple points:

| Stage | Validation Focus |
|---|---|
| Raw import | Row counts, source file completeness, duplicate records |
| Staging | Date conversion, numeric conversion, required fields |
| Core tables | Account joins, security joins, transaction classification |
| Ledger | Cash roll-forward tie-outs, negative balances |
| Positions | Share roll-forward tie-outs, negative share checks |
| Custodian simulation | Injection counts, file linkage, clean vs modified records |
| Reconciliation | Break type accuracy, variance calculations, missing records |
| Exception log | Root cause, owner, SLA status, severity, exposure completeness |
| Excel | SQL tie-outs, formula checks, dashboard support |
| Power BI | KPI tie-outs, relationship checks, formatting checks |
| Python | Data quality, anomaly detection, vendor validation |
| Controls | Evidence mapping, owner, frequency, review status |

---

## 17. Limitations

This data flow represents a simulated portfolio project. It does not represent a live broker-dealer system, production reconciliation process, real custodian feed, regulatory filing process, or certified compliance system.

Synthetic records and controlled exceptions are used to demonstrate financial operations workflows in a recruiter-ready format.
