-- ==============================================================================
-- Script: 07_validation_checks.sql
-- Purpose: Data quality rules and post-load validation testing.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- We will output validation results to a temporary holding table or just query them out.
-- For production, these would insert into ctl.validation_results or raise errors.

-- 1. Row Count Check (Raw vs Staging)
SELECT 
    'Row Count Validation' AS CheckName,
    (SELECT COUNT(*) FROM raw.raw_stock_transactions) AS RawCount,
    (SELECT COUNT(*) FROM stg.vw_stock_transactions_clean) AS StagingCount,
    CASE 
        WHEN (SELECT COUNT(*) FROM raw.raw_stock_transactions) = (SELECT COUNT(*) FROM stg.vw_stock_transactions_clean) THEN 'PASS'
        ELSE 'FAIL'
    END AS Status;

-- 2. Duplicate Source Transaction IDs
SELECT 
    'Duplicate ID Check' AS CheckName,
    source_transaction_id,
    COUNT(*) as Occurrences
FROM stg.vw_stock_transactions_clean
GROUP BY source_transaction_id
HAVING COUNT(*) > 1;

-- 3. Failed Date Conversions
SELECT 
    'Failed Date Casts' AS CheckName,
    COUNT(*) AS FailedCount
FROM stg.vw_stock_transactions_clean
WHERE flag_invalid_date = 1;

-- 4. Failed Amount Conversions
SELECT 
    'Failed Amount Casts' AS CheckName,
    COUNT(*) AS FailedCount
FROM stg.vw_stock_transactions_clean
WHERE flag_invalid_amount = 1;

-- 5. Missing Required Account/Transaction Fields
SELECT 
    'Missing Required Fields' AS CheckName,
    COUNT(*) AS MissingFieldsCount
FROM stg.vw_stock_transactions_clean
WHERE synthetic_account_id IS NULL
   OR raw_action IS NULL;

-- 6. Unclassified Transaction Actions
SELECT 
    'Unmapped Actions' AS CheckName,
    s.raw_action,
    COUNT(*) AS Occurrences
FROM stg.vw_stock_transactions_clean s
LEFT JOIN stg.transaction_type_mapping m ON s.raw_action = m.raw_action
WHERE m.standardized_category IS NULL
GROUP BY s.raw_action;

-- 7. Broken Joins (Securities)
SELECT 
    'Broken Security Joins' AS CheckName,
    COUNT(*) AS BrokenJoinsCount
FROM core.security_transactions s
LEFT JOIN core.securities sec ON s.ticker = sec.ticker
WHERE sec.ticker IS NULL;
GO
