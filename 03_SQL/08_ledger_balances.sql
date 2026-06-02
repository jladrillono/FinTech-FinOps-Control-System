-- ==============================================================================
-- Script: 08_ledger_balances.sql
-- Purpose: Calculates daily continuous cash ledger balances.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

TRUNCATE TABLE core.internal_ledger_balances;
GO

-- 1. Determine the boundary dates from cash activity
DECLARE @MinDate DATE, @MaxDate DATE;
SELECT @MinDate = MIN(transaction_date), @MaxDate = MAX(transaction_date) 
FROM core.cash_transactions;

-- If there are no transactions, exit
IF @MinDate IS NULL RETURN;

-- 2. Build a continuous calendar CTE
WITH Calendar AS (
    SELECT @MinDate AS CalendarDate
    UNION ALL
    SELECT DATEADD(day, 1, CalendarDate)
    FROM Calendar
    WHERE CalendarDate < @MaxDate
),
-- 3. Calculate daily net cash flows per account
DailyNetFlows AS (
    SELECT 
        account_id,
        transaction_date,
        SUM(cash_impact) AS daily_net_cash
    FROM core.cash_transactions
    GROUP BY account_id, transaction_date
),
-- 4. Create a dense grid of all dates and all active accounts
AccountGrid AS (
    SELECT a.account_id, c.CalendarDate
    FROM core.accounts a
    CROSS JOIN Calendar c
),
-- 5. Join grid with flows and calculate running total
RunningBalances AS (
    SELECT 
        g.CalendarDate AS ledger_date,
        g.account_id,
        ISNULL(f.daily_net_cash, 0) AS daily_net_cash,
        SUM(ISNULL(f.daily_net_cash, 0)) OVER (
            PARTITION BY g.account_id 
            ORDER BY g.CalendarDate 
            ROWS UNBOUNDED PRECEDING
        ) AS cash_balance
    FROM AccountGrid g
    LEFT JOIN DailyNetFlows f ON g.account_id = f.account_id AND g.CalendarDate = f.transaction_date
)
-- 6. Insert final balances
INSERT INTO core.internal_ledger_balances (ledger_date, account_id, cash_balance)
SELECT 
    ledger_date,
    account_id,
    cash_balance
FROM RunningBalances
OPTION (MAXRECURSION 32767); -- To allow calendar generation beyond 100 days
GO
