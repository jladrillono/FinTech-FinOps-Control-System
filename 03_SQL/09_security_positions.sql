-- ==============================================================================
-- Script: 09_security_positions.sql
-- Purpose: Calculates daily continuous security share positions.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

TRUNCATE TABLE core.positions;
GO

-- 1. Determine the boundary dates from security activity
DECLARE @MinDate DATE, @MaxDate DATE;
SELECT @MinDate = MIN(transaction_date), @MaxDate = MAX(transaction_date) 
FROM core.security_transactions;

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
-- 3. Calculate daily net share movements per account and ticker
DailyNetShares AS (
    SELECT 
        account_id,
        ticker,
        transaction_date,
        SUM(security_impact) AS daily_net_shares
    FROM core.security_transactions
    GROUP BY account_id, ticker, transaction_date
),
-- 4. Create a dense grid of all dates and all active account-ticker combinations
-- To prevent unnecessary rows before an account first trades a ticker, we find the first trade date
FirstTrade AS (
    SELECT account_id, ticker, MIN(transaction_date) AS first_trade_date
    FROM core.security_transactions
    GROUP BY account_id, ticker
),
PositionGrid AS (
    SELECT ft.account_id, ft.ticker, c.CalendarDate
    FROM FirstTrade ft
    JOIN Calendar c ON c.CalendarDate >= ft.first_trade_date
),
-- 5. Join grid with flows and calculate running total
RunningPositions AS (
    SELECT 
        g.CalendarDate AS position_date,
        g.account_id,
        g.ticker,
        ISNULL(f.daily_net_shares, 0) AS daily_net_shares,
        SUM(ISNULL(f.daily_net_shares, 0)) OVER (
            PARTITION BY g.account_id, g.ticker
            ORDER BY g.CalendarDate 
            ROWS UNBOUNDED PRECEDING
        ) AS share_quantity
    FROM PositionGrid g
    LEFT JOIN DailyNetShares f 
        ON g.account_id = f.account_id 
        AND g.ticker = f.ticker 
        AND g.CalendarDate = f.transaction_date
)
-- 6. Insert final positions
INSERT INTO core.positions (position_date, account_id, ticker, share_quantity)
SELECT 
    position_date,
    account_id,
    ticker,
    share_quantity
FROM RunningPositions
WHERE share_quantity <> 0 OR daily_net_shares <> 0 -- Optionally filter out 0 balances if space is an issue, but we'll keep them for clean audits unless told otherwise. We will insert all rows for the grid.
OPTION (MAXRECURSION 32767);
GO
