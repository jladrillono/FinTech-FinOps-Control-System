# Methodology

## Project Title

**FinTech Financial Operations Control & Reconciliation System**

## Executive Methodology Summary

This project simulates a financial operations control environment for a fintech investment platform. The methodology follows an end-to-end operating workflow: raw transaction intake, SQL data modeling, transaction classification, ledger and position roll-forward logic, simulated custodian comparison, reconciliation break detection, Excel review, Power BI management reporting, Python validation, and control documentation.

The project was designed to demonstrate how financial operations teams can use structured data, validation checks, dashboards, exception tracking, and control evidence to monitor customer cash balances, security positions, vendor files, reconciliation breaks, and operational risk.

This is a simulated portfolio project. It does not use live customer data, production brokerage systems, real custodian feeds, trading APIs, regulatory filings, or production compliance infrastructure.

---

## 1. Business Context

A fintech investment platform processes activity such as deposits, withdrawals, dividends, market buys, market sells, fees, taxes, and security movements. In a financial operations environment, internal platform records must be reconciled against external custodian or vendor records to confirm that customer cash and security positions are accurate.

The project addresses the operational risk that internal records, external records, and management reporting can become misaligned if data is not classified, validated, reconciled, and documented consistently.

The methodology was built around three core business questions:

1. Are internal cash balances and security positions calculated correctly from transaction activity?
2. Do internal records match simulated external custodian records?
3. Are exceptions, controls, validation checks, and management reports traceable to supporting evidence?

---

## 2. Scope

## Included

The project includes:

- Raw transaction review
- SQL database design
- Raw, staging, core, reporting, and control layers
- Transaction classification
- Cash impact and security impact logic
- Internal cash ledger roll-forward
- Security position roll-forward
- Simulated custodian balances and positions
- Controlled exception injection
- Reconciliation break detection
- Exception log creation
- SLA, aging, severity, status, root cause, owner, and exposure fields
- Excel reconciliation model
- Power BI dashboard
- Python anomaly detection and data validation outputs
- Control matrix and books-and-records awareness
- Repository documentation and portfolio packaging

## Excluded

The project excludes:

- Live customer data
- Live brokerage data
- Production custodian feeds
- Trading APIs
- Real money movement
- Investment recommendations
- Regulatory submissions
- Production broker-dealer compliance certification
- Formal audit attestation

---

## 3. Data Methodology

## Source Data

The project begins with brokerage-style stock transaction data. The source data was treated as the raw operational input and was not overwritten during transformation. The raw data supports later transaction classification, ledger calculations, position calculations, reconciliation, and exception reporting.

## Synthetic Operating Tables

To create a complete financial operations workflow, the project also uses synthetic or simulated operating tables such as:

- Customers
- Accounts
- Custodian balances
- Custodian positions
- Vendor files
- Reconciliation breaks
- Exception logs
- Control matrix records
- Books-and-records index records

These tables are used to simulate the operational environment around the transaction data.

## Data Quality Focus

The project reviews data quality risks that could affect financial operations outputs, including:

- Missing transaction IDs
- Duplicate transaction IDs
- Duplicate full rows
- Missing tickers
- Missing share quantities
- Missing prices
- Missing or invalid dates
- Incorrect signs
- Broken joins
- Missing account references
- Missing vendor files
- Inconsistent status fields

Data quality findings were treated as operational risk indicators because incorrect source records can affect cash balances, share positions, exception counts, dashboard KPIs, and control evidence.

---

## 4. SQL Methodology

## Purpose of the SQL Layer

SQL Server is the primary data modeling and transformation layer. The SQL methodology separates the project into logical layers so that raw data is preserved, transformations are traceable, and reporting outputs are reusable.

## SQL Architecture

The SQL model uses the following design pattern:

| Layer | Purpose |
|---|---|
| Raw | Preserve original source records with minimal transformation |
| Staging | Clean, type, standardize, and validate source fields |
| Core | Store business-ready transactions, balances, positions, exceptions, and control tables |
| Reporting | Expose stable views for Excel, Power BI, Python, and review outputs |
| Control | Store validation results, control evidence, and books-and-records style documentation |

## Key SQL Methods

The SQL layer uses:

- Table creation scripts
- Primary keys and foreign keys where practical
- Standardized naming conventions
- Data type selection for dates, currency, prices, quantities, and text fields
- CASE logic for transaction classification
- Cash impact calculations
- Security impact calculations
- Aggregations by account, date, ticker, and break type
- Window functions for running balance logic
- Full outer joins for reconciliation matching
- COALESCE logic for unmatched internal or custodian records
- Validation checks for missing records, duplicates, failed joins, and incorrect signs
- Reporting views for downstream tools

## SQL Outputs

The SQL layer creates or supports:

- Cash transaction outputs
- Security transaction outputs
- Internal ledger balances
- Security positions
- Custodian comparison records
- Reconciliation breaks
- Exception logs
- Validation result outputs
- Reporting views for Excel and Power BI

---

## 5. Transaction Classification Methodology

Raw transaction activity is mapped into standardized financial operations categories. Each category is assigned expected cash and security impact logic.

| Transaction Category | Cash Impact | Security Impact |
|---|---:|---:|
| Deposit | Increase cash | No share impact |
| Withdrawal | Decrease cash | No share impact |
| Dividend | Increase cash | No share impact unless reinvestment is modeled |
| Market Buy | Decrease cash | Increase shares |
| Market Sell | Increase cash | Decrease shares |
| Fee | Decrease cash | No share impact |
| Tax | Decrease cash | No share impact |
| Adjustment | Depends on business rule | Depends on business rule |
| Needs Review | Requires review | Requires review |

This classification methodology supports ledger calculation, position calculation, reconciliation, dashboard reporting, and control review.

---

## 6. Ledger and Position Methodology

## Cash Ledger Roll-Forward

The cash ledger methodology calculates internal cash balances by account and business date.

The logic follows this business formula:

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

The SQL layer aggregates cash movements and uses running balance logic to calculate ending cash balances over time.

## Security Position Roll-Forward

The security position methodology calculates account-level security positions by ticker and date.

The logic follows this business formula:

```text
Beginning Shares
+ Shares Purchased
- Shares Sold
= Ending Shares
```

Security positions are calculated separately from cash balances because share movements and cash movements affect different operational records.

---

## 7. Custodian Simulation Methodology

The project simulates external custodian records from internal ledger and position outputs. This allows the reconciliation process to compare internal records against an external source.

## Baseline Custodian Records

Baseline custodian records are generated from internal balances and positions. These records represent the external source before controlled exceptions are introduced.

## Controlled Exception Injection

Controlled exceptions are intentionally added to test whether the reconciliation logic detects known issues. Each controlled exception should be traceable by account, date, table, record type, expected detection rule, and business impact.

Examples include:

- Cash balance breaks
- Share quantity breaks
- Missing records
- Duplicate records
- Timing differences
- Fee mismatches
- Dividend mismatches
- Wrong-account postings
- Missing or late vendor files

The purpose is not to create random errors. The purpose is to simulate realistic financial operations break scenarios in a controlled and explainable way.

---

## 8. Reconciliation and Exception Methodology

## Reconciliation Design

The reconciliation process compares internal records against simulated custodian records. The methodology focuses on identifying differences, classifying the break type, assigning likely root cause, calculating exposure, and creating exception-ready outputs.

## Break Categories

The reconciliation logic supports categories such as:

- Cash balance break
- Share quantity break
- Missing in custodian
- Missing in internal records
- Duplicate transaction
- Timing difference
- Value mismatch
- Unusual balance flag

## Exception Log Fields

The exception log is designed as an operational tracker, not just an error list. Key fields include:

- Exception ID
- Break ID
- Business date
- Account ID
- Ticker or security ID
- Break type
- Severity
- Internal value
- Custodian value
- Variance amount or quantity
- Dollar exposure
- Root cause
- Owner
- Status
- Detected date
- Due date
- Aging days
- SLA status
- Resolution notes
- Evidence file

This structure allows exceptions to be reviewed by operational priority rather than appearing as raw mismatches.

---

## 9. Excel Methodology

## Purpose of the Excel Model

Excel acts as the transparent manual review layer. The workbook allows a reviewer to inspect reconciliation outputs, trace dashboard metrics, validate exception aging, and review control summaries without reading every SQL script.

## Workbook Design

The Excel workbook separates documentation, source data, calculations, checks, and outputs. The workbook includes 16 structured tabs, including instructions, data tabs, dashboard, tie-outs, exception aging, control summary, reconciliation review, injection validation, and ledger validation.

## Excel Methods Used

The Excel model uses:

- Structured tables
- Formula-driven variance checks
- Pass/fail logic
- Tie-out checks
- Exception aging calculations
- SLA classification
- PivotTables or summary tables
- Conditional formatting
- Control summaries
- Dashboard summaries
- Validation tabs

## Excel Validation Purpose

The Excel model helps prove that outputs are not unsupported dashboard numbers. It provides a traceable review layer between SQL outputs and final management reporting.

---

## 10. Power BI Methodology

## Purpose of the Dashboard

Power BI converts reconciliation and validation outputs into management-ready reporting. The dashboard is designed to help management understand operational status, unresolved risk, exposure, aging, root causes, controls, and anomaly results.

## Dashboard Pages

The dashboard includes seven report pages:

1. Executive Overview
2. Cash Monitoring
3. Security Reconciliation
4. Exception Management
5. Controls
6. Validation
7. Python Validation & Anomaly Monitoring

## Dashboard Design Principles

The dashboard methodology follows these principles:

- Each page answers a specific management question.
- KPI cards summarize the most important metrics.
- Trend and bar charts explain direction, concentration, and root cause.
- Detail tables are used only where review detail is necessary.
- Slicers support investigation without overwhelming the page.
- Formatting is kept consistent across pages.
- Metrics should tie back to SQL and Excel outputs.

## Dashboard Measures

Representative dashboard measures include:

- Total transactions
- Accounts reviewed
- Total reconciliation breaks
- Total exceptions
- Open exceptions
- Breaks over SLA
- Dollar exposure
- Control pass rate
- Average exception age
- Data quality pass rate
- Vendor validation issue count
- Python anomaly count
- High-risk anomaly count

---

## 11. Python Methodology

## Purpose of Python Enhancement

Python adds automated validation and anomaly monitoring to strengthen the project’s control environment. The Python layer is used to detect unusual activity and data quality issues that may not be visible through manual review alone.

## Python Output Files

The Python layer produces:

- `anomaly_flags.csv`
- `anomaly_summary.csv`
- `data_quality_results.csv`
- `python_validation_summary.csv`
- `vendor_validation_results.csv`

## Python Methods Used

The Python methodology includes:

- CSV input loading
- Schema validation
- Required column checks
- Date parsing checks
- Numeric conversion checks
- Duplicate record detection
- Missing field detection
- Vendor file validation
- Negative balance checks
- Excess balance checks
- Large movement checks
- IQR-based outlier detection
- Z-score outlier detection
- Severity assignment
- Reason codes
- Review action fields
- Summary output generation

## Python Findings Reviewed

The reviewed Python outputs showed:

- 55,788 anomaly flags
- 5,984 high-risk anomalies
- 63 vendor validation issues
- 76 data quality checks
- 6 failed data quality checks
- 92.1% data quality pass rate

The data quality failures were primarily concentrated in the raw transaction file and included missing transaction IDs, duplicate IDs, missing ticker values, missing share quantities, missing price fields, and duplicate full rows.

## Python Interpretation

Python anomaly flags are not automatic errors. They are review indicators. A flagged record requires review to determine whether it is caused by valid business activity, timing, simulation design, injected exceptions, or a true data issue.

---

## 12. Control Methodology

## Purpose of Controls

The control methodology connects business risks to control activities, evidence, ownership, frequency, and review status.

## Core Control Areas

The project control framework includes:

- Raw data completeness review
- Transaction classification review
- Daily cash roll-forward tie-out
- Security position roll-forward tie-out
- Custodian-to-ledger reconciliation
- Exception aging review
- Duplicate and missing record check
- Vendor file validation
- Dashboard KPI validation
- Evidence retention review
- Executive summary review

## Evidence Retention

The project uses a books-and-records style evidence approach by documenting:

- Evidence type
- Source system or file
- Evidence location
- Owner
- Retention rationale
- Audit-trail relevance
- Review status
- Last reviewed date

This demonstrates that operational analysis should be supported by retained evidence, not just final charts.

---

## 13. Validation Methodology

Validation is applied across SQL, Excel, Power BI, and Python.

## SQL Validation

SQL validation checks include:

- Raw row count to staged row count
- Duplicate transaction IDs
- Missing required fields
- Failed date conversions
- Failed numeric conversions
- Broken account joins
- Broken security joins
- Incorrect sign logic
- Unclassified transaction actions
- Reconciliation variance checks

## Excel Validation

Excel validation checks include:

- Transaction count tie-outs
- Cash total tie-outs
- Security quantity tie-outs
- Internal ledger tie-outs
- Custodian balance tie-outs
- Reconciliation break count tie-outs
- Open exception count tie-outs
- Dollar exposure tie-outs
- SLA status checks
- Injection detection checks
- Ledger roll-forward checks

## Power BI Validation

Power BI validation checks include:

- KPI tie-out to SQL and Excel
- Filter behavior review
- Date relationship review
- Measure logic review
- Dashboard formatting review
- Blank category review
- Percentage formatting review
- Status field review

## Python Validation

Python validation checks include:

- Required file existence
- Required column checks
- Date validity
- Numeric validity
- Duplicate records
- Missing account IDs
- Vendor file completeness
- Anomaly output reason codes
- Summary output pass rates

---

## 14. Assumptions

The methodology uses the following assumptions:

- The project data is simulated or portfolio-based.
- Synthetic account and customer records are used where required.
- Custodian records are simulated for reconciliation testing.
- Controlled exceptions are intentionally introduced for validation.
- Transaction classification rules are based on standard financial operations logic.
- Settlement timing is simplified unless otherwise documented.
- Python thresholds are review thresholds, not production risk limits.
- Dashboard outputs must be validated before being used as final portfolio screenshots.
- Control documentation is designed to demonstrate audit-readiness awareness, not formal compliance certification.

---

## 15. Limitations

This project has several limitations:

- It is not connected to live brokerage systems.
- It does not use live customer information.
- It does not represent actual broker-dealer books and records.
- It does not execute trades or money movement.
- It does not produce regulatory filings.
- It does not represent a certified compliance framework.
- Synthetic data may not reflect all real-world edge cases.
- Python anomaly thresholds require business review before production use.
- Power BI measures depend on correct data relationships and formatting.
- Some exceptions are simulated to demonstrate detection logic.

These limitations are intentional and are documented to keep the project accurate and interview-safe.

---

## 16. Reproducibility Methodology

A reviewer should be able to understand and reproduce the project by following the repository structure and script order.

## Recommended Execution Order

1. Review project overview and README.
2. Review raw data and data dictionary.
3. Run SQL schema scripts.
4. Run SQL staging and transformation scripts.
5. Run ledger and position scripts.
6. Run custodian simulation scripts.
7. Run reconciliation and exception scripts.
8. Run SQL validation checks.
9. Open Excel reconciliation model.
10. Review Excel tie-outs and validation tabs.
11. Open Power BI dashboard.
12. Validate dashboard KPIs against SQL and Excel.
13. Run Python validation scripts.
14. Review anomaly and validation output CSVs.
15. Review control matrix and books-and-records index.
16. Review final executive summary and portfolio screenshots.

---

## 17. Business Value

The methodology demonstrates a controlled financial operations workflow that turns raw transaction data into operational evidence.

The project shows how an analyst can:

- Create structured data models
- Apply transaction classification logic
- Calculate ledger and position balances
- Compare internal and external records
- Identify reconciliation breaks
- Track exceptions by root cause and severity
- Monitor SLA and aging risk
- Validate vendor files
- Detect anomalies with Python
- Build management dashboards
- Document controls and evidence
- Package the work for recruiter and hiring-manager review

---

## 18. Recruiter-Facing Summary

This project demonstrates an end-to-end financial operations reconciliation workflow using SQL Server, Excel, Power BI, Python, and documentation. The system classifies brokerage-style transactions, calculates internal cash and security positions, simulates custodian records, detects reconciliation breaks, tracks exceptions, validates outputs, monitors anomalies, and communicates operational risk through dashboard reporting and control evidence.

It is designed as a simulated portfolio project to show practical skills in financial operations, reconciliation, data validation, exception management, dashboard reporting, and audit-ready documentation.
