INSERT INTO ctl.control_matrix
(
    process_area,
    risk_description,
    control_activity,
    owner,
    evidence_required,
    frequency
)
SELECT *
FROM
(
    VALUES
    ('Data Intake',
     'Missing or incomplete raw transaction data could cause misstated balances.',
     'Review raw transaction record counts and required fields before transformation.',
     'Financial Operations Analyst',
     'raw_stock_transactions row count validation',
     'Daily'),

    ('Transaction Classification',
     'Transactions could be classified incorrectly between cash and security activity.',
     'Validate transaction type mapping and confirm cash and share impact logic.',
     'Financial Operations Analyst',
     'transaction_type_mapping and validation_checks.sql',
     'Daily'),

    ('Cash Ledger',
     'Internal cash balances could be inaccurate due to incorrect sign logic or missing activity.',
     'Recalculate daily cash roll-forward by account and compare totals to cash transactions.',
     'Financial Operations Analyst',
     'daily_cash_rollforward.sql and internal_ledger output',
     'Daily'),

    ('Security Positions',
     'Share quantities could be inaccurate by account or ticker.',
     'Recalculate daily security positions and validate cumulative share balances.',
     'Investment Operations Analyst',
     'security_position_rollforward.sql and positions output',
     'Daily'),

    ('Custodian Reconciliation',
     'Internal ledger records may not match simulated custodian records.',
     'Compare internal ledger and position records to custodian balances and positions.',
     'Reconciliation Analyst',
     'daily_cash_reconciliation.sql and security_position_reconciliation.sql',
     'Daily'),

    ('Exception Management',
     'Open reconciliation breaks could remain unresolved beyond SLA.',
     'Review open exceptions, aging days, owner assignment, and SLA status.',
     'Operations Analyst',
     'exception_log and reconciliation_breaks output',
     'Daily'),

    ('Duplicate and Missing Records',
     'Duplicate or missing records could create false breaks or misstated balances.',
     'Run duplicate transaction, missing account, missing file, and orphan record checks.',
     'Financial Operations Analyst',
     'validation_checks.sql and python_validation_summary.csv',
     'Daily'),

    ('Vendor File Monitoring',
     'Late or missing custodian files could make the reconciliation incomplete.',
     'Validate expected vendor files, receipt status, record counts, and control totals.',
     'Operations Analyst',
     'vendor_files table and vendor_validation_results.csv',
     'Daily'),

    ('Dashboard KPI Validation',
     'Power BI dashboard KPIs could misstate operational performance.',
     'Tie dashboard measures to SQL and Excel source totals before final reporting.',
     'Business Analyst',
     'KPI validation checklist and Dashboard_Notes.md',
     'Monthly'),

    ('Evidence Retention',
     'Control evidence may be incomplete, hard to locate, or not review-ready.',
     'Review evidence inventory and confirm key project outputs are retained in documented locations.',
     'FinOps Control Owner',
     'books_records_index and Evidence_Index.xlsx',
     'Monthly')
) AS v
(
    process_area,
    risk_description,
    control_activity,
    owner,
    evidence_required,
    frequency
)
WHERE NOT EXISTS
(
    SELECT 1
    FROM ctl.control_matrix cm
    WHERE cm.control_activity = v.control_activity
);