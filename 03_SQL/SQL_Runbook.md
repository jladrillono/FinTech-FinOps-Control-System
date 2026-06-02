# SQL Runbook

## Project Title

**FinTech Financial Operations Control & Reconciliation System**

## Purpose

This runbook explains how to execute and review the SQL layer for the FinTech Financial Operations Control & Reconciliation System.

The SQL layer transforms raw brokerage-style transaction data into structured financial operations outputs used for cash activity, security activity, ledger balances, security positions, custodian simulation, reconciliation breaks, exception management, Excel review, Power BI reporting, Python validation, and control documentation.

---

## 1. Database Overview

## Database Name

```sql
FinOps_Control_System
```

## SQL Architecture

The database uses the following schemas:

| Schema | Purpose |
|---|---|
| `raw` | Preserves original imported source records |
| `stg` | Cleans, standardizes, maps, and validates raw transaction data |
| `core` | Stores business-ready financial operations tables |
| `rpt` | Provides reporting views for Excel, Power BI, and portfolio evidence |
| `ctl` | Stores control, vendor, validation, injection, and evidence-related tables |

---

## 2. Main Database Objects

## Raw Layer

| Object | Purpose |
|---|---|
| `raw.raw_stock_transactions` | Original imported transaction source table |

## Staging Layer

| Object | Purpose |
|---|---|
| `stg.transaction_type_mapping` | Maps raw transaction actions to financial operations categories |
| `stg.vw_stock_transactions_clean` | Cleaned and standardized transaction view |

## Core Layer

| Object | Purpose |
|---|---|
| `core.customers` | Synthetic customer reference table |
| `core.accounts` | Synthetic account reference table |
| `core.securities` | Security master table |
| `core.cash_transactions` | Cleaned cash-impacting transaction records |
| `core.security_transactions` | Cleaned security-impacting transaction records |
| `core.internal_ledger_balances` | Internal cash balance roll-forward output |
| `core.positions` | Internal security position roll-forward output |
| `core.custodian_balances` | Simulated custodian cash balance records |
| `core.custodian_positions` | Simulated custodian security position records |
| `core.reconciliation_breaks` | Detected reconciliation breaks |
| `core.exception_log` | Operational exception tracker |

## Control Layer

| Object | Purpose |
|---|---|
| `ctl.vendor_files` | Vendor file receipt and validation records |
| `ctl.exception_injection_log` | Controlled exception injection inventory |
| `ctl.books_records_index` | Evidence and records inventory |
| `ctl.control_matrix` | Risk-control mapping table |
| `ctl.injection_validation` | Controlled exception detection validation |

## Reporting and Reconciliation Views

| Object | Purpose |
|---|---|
| `core.vw_daily_cash_reconciliation` | Compares internal cash balances against custodian balances |
| `core.vw_security_position_reconciliation` | Compares internal positions against custodian positions |
| `core.vw_transaction_match_reconciliation` | Supports transaction-level matching and break detection |
| `rpt.vw_cash_activity` | Reporting view for cash activity |
| `rpt.vw_security_activity` | Reporting view for security activity |
| `rpt.vw_exception_summary` | Summary view for exception reporting |
| `rpt.vw_reconciliation_summary` | Summary view for reconciliation reporting |

---

## 3. Recommended Script Order

Run scripts in this order when rebuilding the SQL project.

| Step | Script | Purpose |
|---:|---|---|
| 1 | `01_create_database.sql` | Creates the project database |
| 2 | `02_schema.sql` | Creates schemas, tables, views, keys, constraints, and indexes |
| 3 | `03_staging_tables.sql` | Loads or prepares raw and staging objects |
| 4 | `04_core_tables.sql` | Creates or populates core reference and transaction tables |
| 5 | `05_transformations.sql` | Classifies transactions and creates cash/security activity outputs |
| 6 | `06_ledger_position_logic.sql` | Calculates internal ledger balances and security positions |
| 7 | `07_custodian_simulation.sql` | Creates simulated custodian records and vendor file metadata |
| 8 | `08_exception_injection.sql` | Applies controlled exception scenarios |
| 9 | `09_reconciliation_exceptions.sql` | Detects reconciliation breaks and creates exception outputs |
| 10 | `10_reporting_views.sql` | Creates reporting views for Excel, Power BI, and validation |
| 11 | `11_validation_checks.sql` | Runs row count, duplicate, join, sign, tie-out, and injection validation checks |
| 12 | `12_export_evidence.sql` | Optional evidence export queries for portfolio packaging |

If the project uses fewer files, the same order still applies conceptually: create database, create schemas/tables, load data, transform data, calculate balances, simulate custodian records, detect breaks, validate results, then export evidence.

---

## 4. Pre-Execution Checklist

Before running SQL scripts, confirm:

- SQL Server or Azure Data Studio is available.
- The project database name is correct.
- Source CSV files are saved in the expected folder.
- File paths do not contain private credentials.
- Raw transaction file is available.
- Transaction mapping file is available.
- Data dictionary has been reviewed.
- Any existing database copy is backed up or intentionally replaced.
- The script is being run in the correct database context.
- No production or live customer data is included.

---

## 5. Execution Steps

## Step 1: Create the Database

Run:

```sql
01_create_database.sql
```

Expected result:

- Database `FinOps_Control_System` is created.
- Database is available in Object Explorer.

Validation query:

```sql
SELECT name
FROM sys.databases
WHERE name = 'FinOps_Control_System';
```

---

## Step 2: Create Schemas and Objects

Run:

```sql
02_schema.sql
```

Expected result:

The following schemas are created:

- `raw`
- `stg`
- `core`
- `rpt`
- `ctl`

Expected table and view objects are created.

Validation query:

```sql
SELECT name AS schema_name
FROM sys.schemas
WHERE name IN ('raw', 'stg', 'core', 'rpt', 'ctl')
ORDER BY name;
```

---

## Step 3: Validate Table Inventory

Run:

```sql
SELECT
    s.name AS schema_name,
    t.name AS table_name
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
ORDER BY
    s.name,
    t.name;
```

Expected result:

Tables should include:

- `raw.raw_stock_transactions`
- `stg.transaction_type_mapping`
- `core.accounts`
- `core.cash_transactions`
- `core.custodian_balances`
- `core.custodian_positions`
- `core.customers`
- `core.exception_log`
- `core.internal_ledger_balances`
- `core.positions`
- `core.reconciliation_breaks`
- `core.securities`
- `core.security_transactions`
- `ctl.books_records_index`
- `ctl.control_matrix`
- `ctl.exception_injection_log`
- `ctl.injection_validation`
- `ctl.vendor_files`

---

## Step 4: Validate View Inventory

Run:

```sql
SELECT
    s.name AS schema_name,
    v.name AS view_name
FROM sys.views v
JOIN sys.schemas s
    ON v.schema_id = s.schema_id
ORDER BY
    s.name,
    v.name;
```

Expected result:

Views should include:

- `core.vw_daily_cash_reconciliation`
- `core.vw_security_position_reconciliation`
- `core.vw_transaction_match_reconciliation`
- `rpt.vw_cash_activity`
- `rpt.vw_exception_summary`
- `rpt.vw_reconciliation_summary`
- `rpt.vw_security_activity`
- `stg.vw_stock_transactions_clean`

---

## Step 5: Load or Confirm Raw Data

Expected source table:

```sql
raw.raw_stock_transactions
```

Validation query:

```sql
SELECT COUNT(*) AS raw_transaction_count
FROM raw.raw_stock_transactions;
```

Expected result:

- Row count should match the imported source file.
- If the count does not match, check import settings, delimiters, headers, and failed rows.

---

## Step 6: Load or Confirm Transaction Type Mapping

Expected mapping table:

```sql
stg.transaction_type_mapping
```

Validation query:

```sql
SELECT *
FROM stg.transaction_type_mapping
ORDER BY raw_action;
```

Expected result:

- Raw transaction actions should map to standardized categories.
- Each mapped action should define expected cash impact and security impact.

---

## Step 7: Review Cleaned Staging View

Expected staging view:

```sql
stg.vw_stock_transactions_clean
```

Validation query:

```sql
SELECT TOP 100 *
FROM stg.vw_stock_transactions_clean;
```

Review:

- Transaction date fields
- Account fields
- Ticker fields
- Amount fields
- Share fields
- Price fields
- Transaction category
- Cash impact
- Security impact
- Validation flags

---

## Step 8: Review Cash and Security Transactions

Expected tables:

```sql
core.cash_transactions
core.security_transactions
```

Validation queries:

```sql
SELECT COUNT(*) AS cash_transaction_count
FROM core.cash_transactions;

SELECT COUNT(*) AS security_transaction_count
FROM core.security_transactions;
```

Sample review:

```sql
SELECT TOP 100 *
FROM core.cash_transactions
ORDER BY account_id, transaction_date;

SELECT TOP 100 *
FROM core.security_transactions
ORDER BY account_id, ticker, transaction_date;
```

Expected result:

- Cash-impacting transactions are separated from security-impacting transactions.
- Buys, sells, deposits, withdrawals, fees, taxes, and dividends follow expected impact logic.

---

## Step 9: Review Ledger and Position Outputs

Expected tables:

```sql
core.internal_ledger_balances
core.positions
```

Validation queries:

```sql
SELECT TOP 100 *
FROM core.internal_ledger_balances
ORDER BY account_id, business_date;

SELECT TOP 100 *
FROM core.positions
ORDER BY account_id, ticker, business_date;
```

Expected result:

- Internal ledger balances should roll forward by account and business date.
- Security positions should roll forward by account, ticker, and business date.

---

## Step 10: Review Custodian Simulation Outputs

Expected tables:

```sql
core.custodian_balances
core.custodian_positions
ctl.vendor_files
ctl.exception_injection_log
```

Validation queries:

```sql
SELECT COUNT(*) AS custodian_balance_count
FROM core.custodian_balances;

SELECT COUNT(*) AS custodian_position_count
FROM core.custodian_positions;

SELECT *
FROM ctl.vendor_files
ORDER BY expected_file_date, file_type;

SELECT *
FROM ctl.exception_injection_log
ORDER BY injection_id;
```

Expected result:

- Custodian records should be available for cash and position reconciliation.
- Vendor file records should support completeness review.
- Injected exceptions should be documented and traceable.

---

## Step 11: Review Reconciliation Views

Expected views:

```sql
core.vw_daily_cash_reconciliation
core.vw_security_position_reconciliation
core.vw_transaction_match_reconciliation
```

Validation queries:

```sql
SELECT TOP 100 *
FROM core.vw_daily_cash_reconciliation
ORDER BY business_date, account_id;

SELECT TOP 100 *
FROM core.vw_security_position_reconciliation
ORDER BY business_date, account_id, ticker;

SELECT TOP 100 *
FROM core.vw_transaction_match_reconciliation
ORDER BY business_date, account_id;
```

Expected result:

- Cash balances are compared between internal and custodian records.
- Share positions are compared between internal and custodian records.
- Transaction-level differences are identified where applicable.

---

## Step 12: Review Reconciliation Breaks and Exception Log

Expected tables:

```sql
core.reconciliation_breaks
core.exception_log
```

Validation queries:

```sql
SELECT COUNT(*) AS reconciliation_break_count
FROM core.reconciliation_breaks;

SELECT COUNT(*) AS exception_count
FROM core.exception_log;

SELECT TOP 100 *
FROM core.reconciliation_breaks
ORDER BY business_date, break_type;

SELECT TOP 100 *
FROM core.exception_log
ORDER BY severity DESC, aging_days DESC;
```

Expected result:

- Breaks should include business-relevant categories.
- Exceptions should include root cause, owner, SLA status, aging, status, severity, and exposure.

---

## Step 13: Review Reporting Views

Expected views:

```sql
rpt.vw_cash_activity
rpt.vw_security_activity
rpt.vw_exception_summary
rpt.vw_reconciliation_summary
```

Validation queries:

```sql
SELECT TOP 100 *
FROM rpt.vw_cash_activity;

SELECT TOP 100 *
FROM rpt.vw_security_activity;

SELECT TOP 100 *
FROM rpt.vw_exception_summary;

SELECT TOP 100 *
FROM rpt.vw_reconciliation_summary;
```

Expected result:

- Reporting views should be readable and ready for Excel, Power BI, validation exports, and portfolio screenshots.

---

## 6. Standard Evidence Export Queries

## Table Inventory

Export result as:

```text
03_SQL/evidence/table_inventory.csv
```

Query:

```sql
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    c.column_id,
    c.name AS column_name,
    ty.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    CASE 
        WHEN pk.column_id IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END AS is_primary_key
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.columns c
    ON t.object_id = c.object_id
JOIN sys.types ty
    ON c.user_type_id = ty.user_type_id
LEFT JOIN (
    SELECT
        ic.object_id,
        ic.column_id
    FROM sys.indexes i
    JOIN sys.index_columns ic
        ON i.object_id = ic.object_id
       AND i.index_id = ic.index_id
    WHERE i.is_primary_key = 1
) pk
    ON c.object_id = pk.object_id
   AND c.column_id = pk.column_id
ORDER BY
    s.name,
    t.name,
    c.column_id;
```

---

## Row Count Summary

Export result as:

```text
03_SQL/evidence/row_count_summary.csv
```

Query:

```sql
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    SUM(p.rows) AS row_count
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.partitions p
    ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1)
GROUP BY
    s.name,
    t.name
ORDER BY
    s.name,
    t.name;
```

---

## Relationship Map

Export result as:

```text
03_SQL/evidence/relationship_map.csv
```

Query:

```sql
SELECT
    fk.name AS foreign_key_name,
    sch_parent.name AS parent_schema,
    parent_table.name AS parent_table,
    parent_col.name AS parent_column,
    sch_ref.name AS referenced_schema,
    ref_table.name AS referenced_table,
    ref_col.name AS referenced_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables parent_table
    ON fkc.parent_object_id = parent_table.object_id
JOIN sys.schemas sch_parent
    ON parent_table.schema_id = sch_parent.schema_id
JOIN sys.columns parent_col
    ON fkc.parent_object_id = parent_col.object_id
   AND fkc.parent_column_id = parent_col.column_id
JOIN sys.tables ref_table
    ON fkc.referenced_object_id = ref_table.object_id
JOIN sys.schemas sch_ref
    ON ref_table.schema_id = sch_ref.schema_id
JOIN sys.columns ref_col
    ON fkc.referenced_object_id = ref_col.object_id
   AND fkc.referenced_column_id = ref_col.column_id
ORDER BY
    parent_table.name,
    fk.name;
```

---

## View Inventory

Export result as:

```text
03_SQL/evidence/view_inventory.csv
```

Query:

```sql
SELECT
    s.name AS schema_name,
    v.name AS view_name,
    m.definition AS view_definition
FROM sys.views v
JOIN sys.schemas s
    ON v.schema_id = s.schema_id
JOIN sys.sql_modules m
    ON v.object_id = m.object_id
ORDER BY
    s.name,
    v.name;
```

---

## 7. Core Validation Checks

Run these checks before exporting portfolio evidence.

## Duplicate Transaction IDs

```sql
SELECT
    transaction_id,
    COUNT(*) AS duplicate_count
FROM raw.raw_stock_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

## Missing Transaction Dates

```sql
SELECT COUNT(*) AS missing_transaction_date_count
FROM raw.raw_stock_transactions
WHERE transaction_date IS NULL;
```

## Missing Account IDs

```sql
SELECT COUNT(*) AS missing_account_id_count
FROM raw.raw_stock_transactions
WHERE account_id IS NULL;
```

## Unmapped Transaction Types

```sql
SELECT DISTINCT
    r.action
FROM raw.raw_stock_transactions r
LEFT JOIN stg.transaction_type_mapping m
    ON r.action = m.raw_action
WHERE m.raw_action IS NULL
ORDER BY r.action;
```

## Orphan Accounts in Cash Transactions

```sql
SELECT COUNT(*) AS orphan_cash_transaction_count
FROM core.cash_transactions c
LEFT JOIN core.accounts a
    ON c.account_id = a.account_id
WHERE a.account_id IS NULL;
```

## Orphan Accounts in Security Transactions

```sql
SELECT COUNT(*) AS orphan_security_transaction_count
FROM core.security_transactions s
LEFT JOIN core.accounts a
    ON s.account_id = a.account_id
WHERE a.account_id IS NULL;
```

## Negative Share Positions

```sql
SELECT *
FROM core.positions
WHERE ending_shares < 0
ORDER BY business_date, account_id, ticker;
```

## Open Exceptions Over SLA

```sql
SELECT *
FROM core.exception_log
WHERE status <> 'Closed'
  AND sla_status = 'Over SLA'
ORDER BY aging_days DESC;
```

---

## 8. Portfolio Screenshot Checklist

Capture screenshots of:

1. Database schemas in Object Explorer
2. Table inventory query result
3. Row count summary query result
4. Relationship map or database diagram
5. Clean staging view sample
6. Cash transaction output
7. Security transaction output
8. Internal ledger balances
9. Position output
10. Custodian balance output
11. Reconciliation view output
12. Reconciliation breaks table
13. Exception log table
14. Validation query result
15. Reporting view output

Save screenshots to:

```text
10_Documentation/screenshots/sql/
```

---

## 9. Expected Evidence Files

Create or export the following evidence files:

```text
03_SQL/evidence/table_inventory.csv
03_SQL/evidence/row_count_summary.csv
03_SQL/evidence/relationship_map.csv
03_SQL/evidence/view_inventory.csv
03_SQL/evidence/validation_results.csv
03_SQL/evidence/sample_cash_reconciliation.csv
03_SQL/evidence/sample_security_reconciliation.csv
03_SQL/evidence/sample_exception_log.csv
```

---

## 10. Common Issues and Fixes

## Issue: Object already exists

Cause:

- Script has already been run.
- Existing database objects were not dropped before rerun.

Fix:

- Use a clean database copy, or
- Add controlled `DROP IF EXISTS` logic, or
- Run only the scripts needed for the current step.

## Issue: Foreign key error

Cause:

- Parent table was not populated before child table.
- Account, customer, or security key does not exist.

Fix:

- Confirm script order.
- Load reference tables before transaction tables.
- Run orphan key validation queries.

## Issue: View fails to create

Cause:

- Underlying table or column does not exist.
- Object was created in the wrong schema.
- Column name changed from earlier phase.

Fix:

- Confirm table inventory.
- Confirm schema prefix.
- Review recent schema changes.

## Issue: Power BI KPI does not match SQL

Cause:

- Power BI relationship issue.
- Incorrect aggregation.
- Missing filter context.
- Data type mismatch.
- Excel or CSV export is outdated.

Fix:

- Validate SQL output first.
- Refresh Power BI.
- Review DAX measure logic.
- Check relationships and slicers.

## Issue: Blank values in Power BI slicers

Cause:

- Missing dates or unmatched records.
- Date table relationship does not cover all dates.
- Nulls exist in source table.

Fix:

- Run missing date checks.
- Confirm date table range.
- Clean or classify blank values.

---

## 11. Final Review Checklist

Before publishing the SQL layer to GitHub, confirm:

- `02_schema.sql` includes tables, views, schemas, keys, and constraints.
- Raw data is preserved separately from staged/cleaned data.
- Core transaction tables are populated.
- Ledger and position outputs are available.
- Custodian simulation outputs are available.
- Reconciliation breaks are populated.
- Exception log includes root cause, owner, status, SLA, aging, severity, and exposure.
- Reporting views are available for Excel and Power BI.
- Validation checks have been run.
- Evidence CSVs have been exported.
- Screenshots have been captured.
- README references the SQL layer.
- Methodology explains the SQL design.
- No credentials, passwords, connection strings, or private paths are included.
- The project is clearly labeled as simulated portfolio work.

---

## 12. Professional Boundary Statement

This SQL database supports a simulated portfolio project. It does not use live customer data, production brokerage systems, live custodian feeds, trading APIs, regulatory filings, or certified compliance infrastructure.

The SQL layer is intended to demonstrate financial operations data modeling, reconciliation logic, exception management, validation checks, and recruiter-ready documentation.
