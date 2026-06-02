-- ==============================================================================
-- Script: 13_daily_cash_reconciliation.sql
-- Purpose: Compares internal cash balances to custodian cash balances.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

IF OBJECT_ID('core.vw_daily_cash_reconciliation', 'V') IS NOT NULL
    DROP VIEW core.vw_daily_cash_reconciliation;
GO

CREATE VIEW core.vw_daily_cash_reconciliation AS
WITH comparison AS (
    SELECT 
        COALESCE(i.account_id, c.account_id) AS account_id,
        COALESCE(i.ledger_date, c.balance_date) AS business_date,
        i.cash_balance AS internal_cash,
        c.custodian_cash_balance AS custodian_cash,
        COALESCE(i.cash_balance, 0) - COALESCE(c.custodian_cash_balance, 0) AS cash_variance,
        c.injection_id
    FROM core.internal_ledger_balances i
    FULL OUTER JOIN core.custodian_balances c
        ON i.account_id = c.account_id
       AND i.ledger_date = c.balance_date
)
SELECT 
    account_id,
    business_date,
    internal_cash,
    custodian_cash,
    cash_variance,
    CASE
        WHEN internal_cash IS NULL THEN 'MISSING_IN_INTERNAL'
        WHEN custodian_cash IS NULL THEN 'MISSING_IN_CUSTODIAN'
        WHEN ABS(cash_variance) > 0.01 THEN 'CASH_BALANCE_BREAK'
        ELSE 'MATCHED'
    END AS break_type,
    injection_id
FROM comparison;
GO
