-- ==============================================================================
-- Script: 06_reporting_views.sql
-- Purpose: Creates stable reporting views for downstream systems and dashboards.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

IF OBJECT_ID('rpt.vw_cash_activity', 'V') IS NOT NULL DROP VIEW rpt.vw_cash_activity;
GO

CREATE VIEW rpt.vw_cash_activity AS
SELECT 
    c.transaction_id,
    c.source_transaction_id,
    c.account_id,
    a.account_type,
    c.transaction_date,
    c.transaction_type,
    m.standardized_category,
    c.currency_total AS currency,
    c.cash_impact,
    c.total_amount AS gross_amount,
    c.withholding_tax,
    c.charge_amount,
    c.stamp_duty,
    c.notes
FROM core.cash_transactions c
JOIN core.accounts a ON c.account_id = a.account_id
LEFT JOIN stg.transaction_type_mapping m ON c.transaction_type = m.raw_action;
GO

IF OBJECT_ID('rpt.vw_security_activity', 'V') IS NOT NULL DROP VIEW rpt.vw_security_activity;
GO

CREATE VIEW rpt.vw_security_activity AS
SELECT 
    s.transaction_id,
    s.source_transaction_id,
    s.account_id,
    a.account_type,
    s.transaction_date,
    s.ticker,
    sec.security_name,
    s.transaction_type,
    m.standardized_category,
    s.security_impact,
    s.shares AS absolute_shares,
    s.price_per_share,
    s.currency_price,
    s.realized_result
FROM core.security_transactions s
JOIN core.accounts a ON s.account_id = a.account_id
JOIN core.securities sec ON s.ticker = sec.ticker
LEFT JOIN stg.transaction_type_mapping m ON s.transaction_type = m.raw_action;
GO

IF OBJECT_ID('rpt.vw_exception_summary', 'V') IS NOT NULL DROP VIEW rpt.vw_exception_summary;
GO

CREATE VIEW rpt.vw_exception_summary AS
SELECT
    rb.break_category,
    el.root_cause,
    el.severity,
    el.status,
    el.sla_status,
    COUNT(*) AS exception_count,
    SUM(ABS(rb.variance)) AS absolute_variance,
    SUM(rb.dollar_exposure) AS dollar_exposure
FROM core.reconciliation_breaks rb
LEFT JOIN core.exception_log el
    ON rb.break_id = el.break_id
GROUP BY
    rb.break_category,
    el.root_cause,
    el.severity,
    el.status,
    el.sla_status;
GO

IF OBJECT_ID('rpt.vw_reconciliation_summary', 'V') IS NOT NULL DROP VIEW rpt.vw_reconciliation_summary;
GO

CREATE VIEW rpt.vw_reconciliation_summary AS
SELECT 
    business_date,
    break_category,
    COUNT(*) AS total_breaks,
    SUM(ABS(variance)) AS total_absolute_variance,
    SUM(dollar_exposure) AS total_dollar_exposure
FROM core.reconciliation_breaks
GROUP BY business_date, break_category;
GO

IF OBJECT_ID('rpt.vw_exposure_summary', 'V') IS NOT NULL DROP VIEW rpt.vw_exposure_summary;
GO

CREATE VIEW rpt.vw_exposure_summary AS
SELECT 
    'Source-level injected exposure' AS exposure_metric,
    'Original simulated error amount or share impact from the exception injection log' AS definition,
    SUM(ABS(expected_impact)) AS total_value
FROM ctl.exception_injection_log
UNION ALL
SELECT 
    'Daily detected exposure' AS exposure_metric,
    'Exposure on a specific account/date/ticker break record' AS definition,
    SUM(dollar_exposure) AS total_value
FROM core.reconciliation_breaks
UNION ALL
SELECT 
    'Cumulative detected exposure' AS exposure_metric,
    'Sum of all detected daily break exposures across the test period' AS definition,
    SUM(dollar_exposure) AS total_value
FROM core.exception_log
UNION ALL
SELECT 
    'Current open exposure' AS exposure_metric,
    'Unresolved exposure as of the simulated review date, deduplicated to current affected positions/balances' AS definition,
    SUM(dollar_exposure) AS total_value
FROM core.exception_log
WHERE status IN ('OPEN', 'IN_REVIEW', 'PENDING_VENDOR');
GO
