-- ==============================================================================
-- Script: 15_transaction_match_reconciliation.sql
-- Purpose: Analyzes balance variances to detect transaction-level root causes.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

IF OBJECT_ID('core.vw_transaction_match_reconciliation', 'V') IS NOT NULL
    DROP VIEW core.vw_transaction_match_reconciliation;
GO

CREATE VIEW core.vw_transaction_match_reconciliation AS
WITH cash_breaks AS (
    SELECT 
        account_id,
        business_date,
        cash_variance,
        internal_cash,
        custodian_cash,
        break_type
    FROM core.vw_daily_cash_reconciliation
    WHERE break_type NOT IN ('MATCHED')
),
-- Match against transactions on the SAME day to find duplicates or missing
same_day_tx AS (
    SELECT 
        cb.account_id,
        cb.business_date,
        cb.cash_variance,
        t.transaction_id,
        t.cash_impact,
        t.transaction_type,
        CASE
            -- If variance exactly equals a transaction amount (internal > custodian), custodian missed it
            WHEN cb.cash_variance = t.cash_impact THEN 'MISSING_IN_CUSTODIAN'
            -- If variance exactly equals negative transaction amount, custodian duplicated it
            WHEN cb.cash_variance = -(t.cash_impact) THEN 'DUPLICATE_TRANSACTION'
            ELSE NULL
        END AS inferred_root_cause
    FROM cash_breaks cb
    LEFT JOIN core.cash_transactions t 
        ON cb.account_id = t.account_id 
       AND cb.business_date = t.transaction_date
),
-- Match against transactions from PREVIOUS days to find timing differences
prev_day_tx AS (
    SELECT 
        cb.account_id,
        cb.business_date,
        cb.cash_variance,
        t.transaction_id,
        t.cash_impact,
        t.transaction_date,
        DATEDIFF(day, t.transaction_date, cb.business_date) AS day_difference
    FROM cash_breaks cb
    JOIN core.cash_transactions t 
        ON cb.account_id = t.account_id 
       -- Checking for transactions within the last 3 days that equal the variance
       AND t.transaction_date >= DATEADD(day, -3, cb.business_date)
       AND t.transaction_date < cb.business_date
    WHERE cb.cash_variance = -(t.cash_impact) -- A previous transaction was finally booked
)
SELECT 
    account_id, 
    business_date, 
    cash_variance, 
    transaction_id, 
    inferred_root_cause 
FROM same_day_tx 
WHERE inferred_root_cause IS NOT NULL
UNION
SELECT 
    account_id, 
    business_date, 
    cash_variance, 
    transaction_id, 
    'TIMING_DIFFERENCE' AS inferred_root_cause
FROM prev_day_tx;
GO
