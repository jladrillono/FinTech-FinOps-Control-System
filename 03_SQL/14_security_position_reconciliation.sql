-- ==============================================================================
-- Script: 14_security_position_reconciliation.sql
-- Purpose: Compares internal security positions to custodian positions.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

IF OBJECT_ID('core.vw_security_position_reconciliation', 'V') IS NOT NULL
    DROP VIEW core.vw_security_position_reconciliation;
GO

CREATE VIEW core.vw_security_position_reconciliation AS
WITH comparison AS (
    SELECT 
        COALESCE(i.account_id, c.account_id) AS account_id,
        COALESCE(i.position_date, c.position_date) AS business_date,
        COALESCE(i.ticker, c.ticker) AS ticker,
        i.share_quantity AS internal_shares,
        c.custodian_share_quantity AS custodian_shares,
        COALESCE(i.share_quantity, 0) - COALESCE(c.custodian_share_quantity, 0) AS share_variance,
        c.injection_id
    FROM core.positions i
    FULL OUTER JOIN core.custodian_positions c
        ON i.account_id = c.account_id
       AND i.position_date = c.position_date
       AND i.ticker = c.ticker
)
SELECT 
    account_id,
    business_date,
    ticker,
    internal_shares,
    custodian_shares,
    share_variance,
    CASE
        WHEN internal_shares IS NULL THEN 'MISSING_IN_INTERNAL'
        WHEN custodian_shares IS NULL THEN 'MISSING_IN_CUSTODIAN'
        WHEN ABS(share_variance) > 0.000001 THEN 'SHARE_QUANTITY_BREAK'
        ELSE 'MATCHED'
    END AS break_type,
    injection_id
FROM comparison;
GO
