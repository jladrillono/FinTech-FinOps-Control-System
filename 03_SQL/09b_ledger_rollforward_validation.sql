-- ==============================================================================
-- Script: 09b_ledger_rollforward_validation.sql
-- Purpose: Validates that prior day balance + daily activity = ending balance
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Ledger Roll-Forward Validation
WITH DailyActivity AS (
    SELECT 
        account_id,
        transaction_date AS activity_date,
        SUM(cash_impact) AS daily_cash_movement
    FROM core.cash_transactions
    GROUP BY account_id, transaction_date
),
RollForward AS (
    SELECT
        curr.account_id,
        curr.ledger_date,
        curr.cash_balance AS ending_balance,
        ISNULL(prev.cash_balance, 0) AS prior_balance,
        ISNULL(act.daily_cash_movement, 0) AS daily_movement,
        ISNULL(prev.cash_balance, 0) + ISNULL(act.daily_cash_movement, 0) AS calculated_ending_balance
    FROM core.internal_ledger_balances curr
    LEFT JOIN core.internal_ledger_balances prev
        ON curr.account_id = prev.account_id 
       AND prev.ledger_date = DATEADD(day, -1, curr.ledger_date)
    LEFT JOIN DailyActivity act
        ON curr.account_id = act.account_id
       AND curr.ledger_date = act.activity_date
)
SELECT 
    'Roll-Forward Failure' AS CheckName,
    account_id,
    ledger_date,
    prior_balance,
    daily_movement,
    calculated_ending_balance,
    ending_balance,
    (calculated_ending_balance - ending_balance) AS variance
FROM RollForward
WHERE ABS(calculated_ending_balance - ending_balance) > 0.001;
GO
