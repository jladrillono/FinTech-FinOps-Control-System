/* 
Purpose:
Inventory schemas, tables, views, and table row counts.
Use this to confirm whether the database has raw, staging, core, reporting, and control layers.
*/

SELECT
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS object_name,
    o.type_desc AS object_type,
    COALESCE(SUM(ps.row_count), 0) AS row_count
FROM sys.objects o
JOIN sys.schemas s
    ON o.schema_id = s.schema_id
LEFT JOIN sys.dm_db_partition_stats ps
    ON o.object_id = ps.object_id
   AND ps.index_id IN (0, 1)
WHERE o.type IN ('U', 'V')
  AND o.is_ms_shipped = 0
GROUP BY
    s.name,
    o.name,
    o.type_desc
ORDER BY
    s.name,
    o.type_desc,
    o.name;

/*
Purpose:
Check whether the required FinOps database objects exist.
Adjust object names if your actual table names differ.
*/

DECLARE @expected_objects TABLE (
    phase_layer varchar(50),
    schema_name sysname,
    object_name sysname,
    expected_type varchar(20),
    priority varchar(20)
);

INSERT INTO @expected_objects VALUES
('Raw',      'raw',  'raw_stock_transactions',       'TABLE', 'Critical'),
('Staging',  'stg',  'stock_transactions_clean',     'TABLE', 'Critical'),
('Staging',  'stg',  'transaction_type_mapping',     'TABLE', 'High'),
('Core',     'core', 'customers',                    'TABLE', 'High'),
('Core',     'core', 'accounts',                     'TABLE', 'Critical'),
('Core',     'core', 'securities',                   'TABLE', 'Critical'),
('Core',     'core', 'cash_transactions',            'TABLE', 'Critical'),
('Core',     'core', 'security_transactions',        'TABLE', 'Critical'),
('Core',     'core', 'internal_ledger_balances',     'TABLE', 'Critical'),
('Core',     'core', 'positions',                    'TABLE', 'Critical'),
('Core',     'core', 'custodian_balances',           'TABLE', 'Critical'),
('Core',     'core', 'custodian_positions',          'TABLE', 'Critical'),
('Core',     'core', 'reconciliation_breaks',        'TABLE', 'Critical'),
('Core',     'core', 'exception_log',                'TABLE', 'Critical'),
('Control',  'ctl',  'control_matrix',               'TABLE', 'High'),
('Control',  'ctl',  'books_records_index',          'TABLE', 'High'),
('Reporting','rpt',  'vw_cash_activity',             'VIEW',  'High'),
('Reporting','rpt',  'vw_security_activity',         'VIEW',  'High'),
('Reporting','rpt',  'vw_reconciliation_summary',    'VIEW',  'High'),
('Reporting','rpt',  'vw_exception_summary',         'VIEW',  'High');

SELECT
    e.phase_layer,
    e.schema_name,
    e.object_name,
    e.expected_type,
    e.priority,
    CASE
        WHEN o.object_id IS NULL THEN 'MISSING'
        ELSE 'FOUND'
    END AS status,
    o.type_desc AS actual_object_type
FROM @expected_objects e
LEFT JOIN sys.schemas s
    ON e.schema_name = s.name
LEFT JOIN sys.objects o
    ON o.schema_id = s.schema_id
   AND o.name = e.object_name
ORDER BY
    CASE e.priority
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        ELSE 3
    END,
    e.phase_layer,
    e.schema_name,
    e.object_name;

	/*
Purpose:
Review every column, data type, precision, scale, nullability, identity flag, and default.
Use this to assess naming discipline and whether dates/money/shares are stored correctly.
*/

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
    c.is_identity,
    dc.definition AS default_definition
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.columns c
    ON t.object_id = c.object_id
JOIN sys.types ty
    ON c.user_type_id = ty.user_type_id
LEFT JOIN sys.default_constraints dc
    ON c.default_object_id = dc.object_id
WHERE s.name IN ('raw', 'stg', 'core', 'rpt', 'ctl', 'dbo')
ORDER BY
    s.name,
    t.name,
    c.column_id;

	/*
Purpose:
Find likely data type problems.
This flags dates stored as text, currency stored as float/text, and share/price fields stored incorrectly.
*/

SELECT
    s.name AS schema_name,
    t.name AS table_name,
    c.name AS column_name,
    ty.name AS data_type,
    c.precision,
    c.scale,
    CASE
        WHEN c.name LIKE '%date%' 
             AND ty.name IN ('varchar', 'nvarchar', 'char', 'nchar')
            THEN 'DATE STORED AS TEXT'

        WHEN (
                c.name LIKE '%amount%' OR
                c.name LIKE '%cash%' OR
                c.name LIKE '%balance%' OR
                c.name LIKE '%exposure%' OR
                c.name LIKE '%variance%' OR
                c.name LIKE '%fee%' OR
                c.name LIKE '%tax%'
             )
             AND ty.name NOT IN ('decimal', 'numeric', 'money', 'smallmoney', 'int', 'bigint')
            THEN 'MONEY/AMOUNT FIELD MAY HAVE WEAK DATA TYPE'

        WHEN (
                c.name LIKE '%share%' OR
                c.name LIKE '%quantity%' OR
                c.name LIKE '%price%'
             )
             AND ty.name NOT IN ('decimal', 'numeric', 'money', 'smallmoney')
            THEN 'SHARES/PRICE FIELD MAY NEED DECIMAL PRECISION'

        WHEN ty.name = 'float'
            THEN 'FLOAT USED - REVIEW FOR FINANCIAL PRECISION RISK'

        WHEN ty.name IN ('varchar', 'nvarchar') AND c.max_length = -1
            THEN 'NVARCHAR(MAX) USED - REVIEW IF INTENTIONAL'

        ELSE 'OK'
    END AS data_type_review
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.columns c
    ON t.object_id = c.object_id
JOIN sys.types ty
    ON c.user_type_id = ty.user_type_id
WHERE s.name IN ('raw', 'stg', 'core', 'ctl', 'dbo')
ORDER BY
    data_type_review DESC,
    s.name,
    t.name,
    c.column_id;

	/*
Purpose:
Review relationship integrity.
A recruiter-ready SQL model should have clear primary keys, foreign keys, uniqueness rules, and useful indexes.
*/

SELECT
    s.name AS schema_name,
    t.name AS table_name,
    i.name AS index_or_key_name,
    i.type_desc,
    i.is_primary_key,
    i.is_unique,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS key_columns
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.indexes i
    ON t.object_id = i.object_id
JOIN sys.index_columns ic
    ON i.object_id = ic.object_id
   AND i.index_id = ic.index_id
JOIN sys.columns c
    ON ic.object_id = c.object_id
   AND ic.column_id = c.column_id
WHERE i.name IS NOT NULL
  AND s.name IN ('raw', 'stg', 'core', 'ctl', 'dbo')
GROUP BY
    s.name,
    t.name,
    i.name,
    i.type_desc,
    i.is_primary_key,
    i.is_unique
ORDER BY
    s.name,
    t.name,
    i.is_primary_key DESC,
    i.is_unique DESC,
    i.name;

	/*
Purpose:
Identify weak table design.
Most core tables should have a primary key.
*/

SELECT
    s.name AS schema_name,
    t.name AS table_name,
    CASE
        WHEN pk.object_id IS NULL THEN 'MISSING PRIMARY KEY'
        ELSE 'HAS PRIMARY KEY'
    END AS primary_key_status
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
LEFT JOIN sys.key_constraints pk
    ON t.object_id = pk.parent_object_id
   AND pk.type = 'PK'
WHERE s.name IN ('raw', 'stg', 'core', 'ctl', 'dbo')
ORDER BY
    primary_key_status DESC,
    s.name,
    t.name;

	/*
Purpose:
Show parent-to-child table relationships.
This is useful for building your ERD and explaining data lineage.
*/

SELECT
    fk.name AS foreign_key_name,
    ps.name AS parent_schema,
    pt.name AS parent_table,
    pc.name AS parent_column,
    rs.name AS referenced_schema,
    rt.name AS referenced_table,
    rc.name AS referenced_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables pt
    ON fkc.parent_object_id = pt.object_id
JOIN sys.schemas ps
    ON pt.schema_id = ps.schema_id
JOIN sys.columns pc
    ON fkc.parent_object_id = pc.object_id
   AND fkc.parent_column_id = pc.column_id
JOIN sys.tables rt
    ON fkc.referenced_object_id = rt.object_id
JOIN sys.schemas rs
    ON rt.schema_id = rs.schema_id
JOIN sys.columns rc
    ON fkc.referenced_object_id = rc.object_id
   AND fkc.referenced_column_id = rc.column_id
ORDER BY
    parent_schema,
    parent_table,
    foreign_key_name;

	/*
Purpose:
Find object and column names that may violate lower_snake_case standards.
This is not perfect, but it quickly identifies obvious naming issues.
*/

SELECT
    'OBJECT' AS issue_type,
    s.name AS schema_name,
    o.name AS object_name,
    NULL AS column_name,
    o.type_desc
FROM sys.objects o
JOIN sys.schemas s
    ON o.schema_id = s.schema_id
WHERE o.is_ms_shipped = 0
  AND o.type IN ('U', 'V')
  AND (
        o.name COLLATE Latin1_General_BIN LIKE '%[A-Z]%'
        OR o.name LIKE '% %'
        OR o.name LIKE '%-%'
      )

UNION ALL

SELECT
    'COLUMN' AS issue_type,
    s.name AS schema_name,
    t.name AS object_name,
    c.name AS column_name,
    'COLUMN' AS type_desc
FROM sys.tables t
JOIN sys.schemas s
    ON t.schema_id = s.schema_id
JOIN sys.columns c
    ON t.object_id = c.object_id
WHERE c.name COLLATE Latin1_General_BIN LIKE '%[A-Z]%'
   OR c.name LIKE '% %'
   OR c.name LIKE '%-%'
ORDER BY
    issue_type,
    schema_name,
    object_name,
    column_name;

	/*
Purpose:
Compare SQL table counts to the Excel model row counts observed in the uploaded workbook.
Update table names if your SQL tables differ.
*/

SELECT 'core.cash_transactions' AS object_name, COUNT(*) AS sql_row_count, 3295 AS excel_row_count
FROM core.cash_transactions

UNION ALL
SELECT 'core.security_transactions', COUNT(*), 1650
FROM core.security_transactions

UNION ALL
SELECT 'core.internal_ledger_balances', COUNT(*), 1524
FROM core.internal_ledger_balances

UNION ALL
SELECT 'core.custodian_balances', COUNT(*), 1524
FROM core.custodian_balances

UNION ALL
SELECT 'core.positions', COUNT(*), 76651
FROM core.positions

UNION ALL
SELECT 'core.custodian_positions', COUNT(*), 76652
FROM core.custodian_positions

UNION ALL
SELECT 'core.reconciliation_breaks', COUNT(*), 2403
FROM core.reconciliation_breaks

UNION ALL
SELECT 'core.exception_log', COUNT(*), 2403
FROM core.exception_log;

/*
Purpose:
Evaluate whether transaction types are mapped cleanly and whether cash/security impacts are directionally correct.
*/

SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(cash_impact) AS total_cash_impact,
    MIN(cash_impact) AS min_cash_impact,
    MAX(cash_impact) AS max_cash_impact
FROM core.cash_transactions
GROUP BY
    transaction_type
ORDER BY
    transaction_count DESC;


SELECT
    transaction_type,
    ticker,
    COUNT(*) AS transaction_count,
    SUM(security_impact) AS total_security_impact,
    MIN(security_impact) AS min_security_impact,
    MAX(security_impact) AS max_security_impact
FROM core.security_transactions
GROUP BY
    transaction_type,
    ticker
ORDER BY
    transaction_type,
    transaction_count DESC;

	/*
Purpose:
Check duplicate IDs and missing required fields in the core operating tables.
*/

-- Duplicate transaction IDs
SELECT
    'cash_transactions' AS table_name,
    transaction_id,
    COUNT(*) AS duplicate_count
FROM core.cash_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'security_transactions' AS table_name,
    transaction_id,
    COUNT(*) AS duplicate_count
FROM core.security_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;


-- Missing required fields
SELECT
    'cash_transactions' AS table_name,
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) AS missing_transaction_id,
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS missing_account_id,
    SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END) AS missing_transaction_date,
    SUM(CASE WHEN transaction_type IS NULL THEN 1 ELSE 0 END) AS missing_transaction_type
FROM core.cash_transactions

UNION ALL

SELECT
    'security_transactions' AS table_name,
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN transaction_type IS NULL THEN 1 ELSE 0 END)
FROM core.security_transactions;

/*
Purpose:
Validate whether daily ledger balances tie to cash movement.
This assumes internal_ledger_balances has account_id, ledger_date, and cash_balance.
*/

WITH daily_cash AS (
    SELECT
        account_id,
        transaction_date AS ledger_date,
        SUM(cash_impact) AS daily_cash_movement
    FROM core.cash_transactions
    GROUP BY
        account_id,
        transaction_date
),
ledger_check AS (
    SELECT
        l.account_id,
        l.ledger_date,
        LAG(l.cash_balance) OVER (
            PARTITION BY l.account_id
            ORDER BY l.ledger_date
        ) AS prior_cash_balance,
        COALESCE(dc.daily_cash_movement, 0) AS daily_cash_movement,
        l.cash_balance AS ending_cash_balance
    FROM core.internal_ledger_balances l
    LEFT JOIN daily_cash dc
        ON l.account_id = dc.account_id
       AND l.ledger_date = dc.ledger_date
)
SELECT
    account_id,
    ledger_date,
    prior_cash_balance,
    daily_cash_movement,
    ending_cash_balance,
    ROUND(
        COALESCE(prior_cash_balance, 0) + daily_cash_movement - ending_cash_balance,
        2
    ) AS tie_out_difference
FROM ledger_check
WHERE ABS(
    ROUND(
        COALESCE(prior_cash_balance, 0) + daily_cash_movement - ending_cash_balance,
        2
    )
) > 0.01
ORDER BY
    account_id,
    ledger_date;

	/*
Purpose:
Recreate the cash reconciliation and compare it to the reconciliation_breaks output.
*/

WITH cash_recon AS (
    SELECT
        COALESCE(i.account_id, c.account_id) AS account_id,
        COALESCE(i.ledger_date, c.balance_date) AS business_date,
        i.cash_balance AS internal_cash_balance,
        c.custodian_cash_balance,
        ROUND(
            COALESCE(i.cash_balance, 0) - COALESCE(c.custodian_cash_balance, 0),
            2
        ) AS cash_variance
    FROM core.internal_ledger_balances i
    FULL OUTER JOIN core.custodian_balances c
        ON i.account_id = c.account_id
       AND i.ledger_date = c.balance_date
)
SELECT
    COUNT(*) AS cash_break_count,
    SUM(ABS(cash_variance)) AS total_absolute_cash_variance,
    SUM(cash_variance) AS net_cash_variance
FROM cash_recon
WHERE ABS(cash_variance) > 0.01
   OR internal_cash_balance IS NULL
   OR custodian_cash_balance IS NULL;



   /*
Purpose:
Recreate the security position reconciliation.
*/

WITH position_recon AS (
    SELECT
        COALESCE(p.account_id, cp.account_id) AS account_id,
        COALESCE(p.position_date, cp.position_date) AS business_date,
        COALESCE(p.ticker, cp.ticker) AS ticker,
        p.share_quantity AS internal_shares,
        cp.custodian_share_quantity,
        ROUND(
            COALESCE(p.share_quantity, 0) - COALESCE(cp.custodian_share_quantity, 0),
            8
        ) AS share_variance
    FROM core.positions p
    FULL OUTER JOIN core.custodian_positions cp
        ON p.account_id = cp.account_id
       AND p.position_date = cp.position_date
       AND p.ticker = cp.ticker
)
SELECT
    COUNT(*) AS position_break_count,
    SUM(ABS(share_variance)) AS total_absolute_share_variance,
    SUM(share_variance) AS net_share_variance
FROM position_recon
WHERE ABS(share_variance) > 0.00000001
   OR internal_shares IS NULL
   OR custodian_share_quantity IS NULL;

   /*
Purpose:
Evaluate whether exception records are operationally complete.
*/

SELECT
    COUNT(*) AS total_exceptions,
    SUM(CASE WHEN break_id IS NULL THEN 1 ELSE 0 END) AS missing_break_id,
    SUM(CASE WHEN account_id IS NULL THEN 1 ELSE 0 END) AS missing_account_id,
    SUM(CASE WHEN break_type IS NULL THEN 1 ELSE 0 END) AS missing_break_type,
    SUM(CASE WHEN severity IS NULL THEN 1 ELSE 0 END) AS missing_severity,
    SUM(CASE WHEN root_cause IS NULL THEN 1 ELSE 0 END) AS missing_root_cause,
    SUM(CASE WHEN owner IS NULL THEN 1 ELSE 0 END) AS missing_owner,
    SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) AS missing_status,
    SUM(CASE WHEN detected_date IS NULL THEN 1 ELSE 0 END) AS missing_detected_date,
    SUM(CASE WHEN due_date IS NULL THEN 1 ELSE 0 END) AS missing_due_date,
    SUM(CASE WHEN aging_days IS NULL THEN 1 ELSE 0 END) AS missing_aging_days,
    SUM(CASE WHEN sla_status IS NULL THEN 1 ELSE 0 END) AS missing_sla_status,
    SUM(CASE WHEN evidence_file IS NULL OR evidence_file = '' THEN 1 ELSE 0 END) AS missing_evidence_file
FROM core.exception_log;

SELECT
    rb.break_category,
    el.root_cause,
    COUNT(*) AS break_count,
    SUM(rb.variance) AS net_cash_variance,
    SUM(ABS(rb.variance)) AS absolute_cash_variance
FROM core.reconciliation_breaks rb
LEFT JOIN core.exception_log el
    ON rb.break_id = el.break_id
WHERE rb.break_category = 'CASH_BALANCE_BREAK'
GROUP BY
    rb.break_category,
    el.root_cause
ORDER BY
    absolute_cash_variance DESC;

SELECT
    rb.ticker,
    COUNT(*) AS break_count,
    SUM(rb.variance) AS net_share_variance,
    SUM(ABS(rb.variance)) AS absolute_share_variance
FROM core.reconciliation_breaks rb
WHERE rb.break_category = 'SHARE_QUANTITY_BREAK'
GROUP BY
    rb.ticker
ORDER BY
    absolute_share_variance DESC;

SELECT
    rb.account_id,
    rb.ticker,
    MIN(rb.business_date) AS first_break_date,
    MAX(rb.business_date) AS last_break_date,
    COUNT(*) AS break_days,
    SUM(rb.variance) AS net_share_variance,
    SUM(ABS(rb.variance)) AS absolute_share_variance
FROM core.reconciliation_breaks rb
WHERE rb.break_category = 'SHARE_QUANTITY_BREAK'
GROUP BY
    rb.account_id,
    rb.ticker
ORDER BY
    break_days DESC;