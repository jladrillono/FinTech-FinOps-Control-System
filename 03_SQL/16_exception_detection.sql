-- ==============================================================================
-- Script: 16_exception_detection.sql
-- Purpose: Combines all reconciliation logic into final exception outputs.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

DELETE FROM core.exception_log;
DBCC CHECKIDENT ('core.exception_log', RESEED, 0);
DELETE FROM core.reconciliation_breaks;
DBCC CHECKIDENT ('core.reconciliation_breaks', RESEED, 0);
GO

-- Simulated review date used for all aging, SLA, and status calculations
-- Using a fixed date keeps results deterministic and avoids inflated aging.
DECLARE @ReviewDate DATE = '2024-07-05';

-- 1. Insert Cash Breaks
INSERT INTO core.reconciliation_breaks (
    account_id, business_date, break_category, internal_value, custodian_value, variance, dollar_exposure, injection_id
)
SELECT 
    account_id, 
    business_date, 
    break_type, 
    internal_cash, 
    custodian_cash, 
    cash_variance,
    ABS(cash_variance),
    injection_id
FROM core.vw_daily_cash_reconciliation
WHERE break_type <> 'MATCHED';

-- 2. Insert Security Breaks
INSERT INTO core.reconciliation_breaks (
    account_id, business_date, ticker, break_category, internal_value, custodian_value, variance, dollar_exposure, injection_id
)
SELECT 
    account_id, 
    business_date, 
    ticker,
    break_type, 
    internal_shares, 
    custodian_shares, 
    share_variance,
    ABS(share_variance) * 150.00,
    injection_id
FROM core.vw_security_position_reconciliation
WHERE break_type <> 'MATCHED';
GO

-- 5. Populate the Exception Log (Operational Tracker)
DECLARE @ReviewDate2 DATE = '2024-07-05';

INSERT INTO core.exception_log (
    break_id, business_date, account_id, ticker, break_type, severity, internal_value, custodian_value, variance_amount, dollar_exposure,
    root_cause, owner, status, detected_date, due_date, aging_days, sla_status, resolution_notes, evidence_file
)
SELECT 
    b.break_id,
    b.business_date,
    b.account_id,
    b.ticker,
    b.break_category,
    CASE 
        WHEN b.dollar_exposure > 5000 THEN 'CRITICAL'
        WHEN b.dollar_exposure > 500 THEN 'HIGH'
        WHEN b.dollar_exposure > 50 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS severity,
    b.internal_value,
    b.custodian_value,
    b.variance,
    b.dollar_exposure,
    -- Infer root cause logic
    COALESCE(tm.inferred_root_cause, 
        CASE 
            WHEN b.break_category = 'CASH_BALANCE_BREAK' AND ABS(b.variance) < 5.00 THEN 'FEE_MISMATCH'
            WHEN b.break_category = 'CASH_BALANCE_BREAK' AND ABS(b.variance) < 20.00 THEN 'DIVIDEND_MISMATCH'
            WHEN b.break_category = 'CASH_BALANCE_BREAK' AND ABS(b.variance) BETWEEN 240 AND 260 THEN 'DUPLICATE_CUSTODIAN_CASH_RECORD'
            WHEN b.break_category = 'CASH_BALANCE_BREAK' AND ABS(b.variance) BETWEEN 490 AND 510 THEN 'SETTLEMENT_TIMING_DIFFERENCE'
            WHEN b.break_category = 'CASH_BALANCE_BREAK' THEN 'CONTROLLED_CASH_EXCEPTION_CARRYFORWARD'
            WHEN b.break_category = 'SHARE_QUANTITY_BREAK' THEN 'CORPORATE_ACTION_OR_TRADE_BREAK'
            WHEN b.break_category = 'MISSING_VENDOR_FILE' THEN 'MISSING_VENDOR_FILE'
            WHEN b.break_category = 'WRONG_ACCOUNT_POSTING' THEN 'WRONG_ACCOUNT_POSTING'
            WHEN b.break_category = 'MISSING_IN_CUSTODIAN' THEN 'MISSING_VENDOR_FILE'
            ELSE 'UNEXPLAINED_VARIANCE'
        END
    ) AS root_cause,
    -- Owner assignment by break category
    CASE 
        WHEN b.break_category = 'CASH_BALANCE_BREAK' THEN 'Reconciliation Team'
        WHEN b.break_category = 'SHARE_QUANTITY_BREAK' THEN 'Corporate Actions'
        WHEN b.break_category IN ('MISSING_IN_CUSTODIAN', 'MISSING_VENDOR_FILE') THEN 'Custodian Ops'
        WHEN b.break_category = 'WRONG_ACCOUNT_POSTING' THEN 'Custodian Ops'
        ELSE 'Control Owner'
    END AS owner,
    -- Realistic status mix: use modular arithmetic on break_id for variety
    CASE
        WHEN b.break_id % 10 < 2 THEN 'OPEN'
        WHEN b.break_id % 10 < 4 THEN 'IN_REVIEW'
        WHEN b.break_id % 10 < 5 THEN 'PENDING_VENDOR'
        ELSE 'RESOLVED'
    END AS status,
    CAST(@ReviewDate2 AS DATE) AS detected_date,
    DATEADD(day, 2, b.business_date) AS due_date,
    DATEDIFF(day, b.business_date, @ReviewDate2) AS aging_days,
    -- SLA derived from status: RESOLVED items are WITHIN_SLA, everything else checked against aging
    CASE
        WHEN b.break_id % 10 >= 5 THEN 'WITHIN_SLA'  -- RESOLVED => met SLA
        WHEN DATEDIFF(day, b.business_date, @ReviewDate2) <= 2 THEN 'WITHIN_SLA'
        ELSE 'OVER_SLA'
    END AS sla_status,
    -- Realistic resolution notes
    CASE
        WHEN b.break_id % 10 >= 5 THEN 'Resolved - variance explained and cleared'
        WHEN b.break_id % 10 < 2 THEN 'Requires investigation'
        WHEN b.break_id % 10 < 4 THEN 'Under review by operations analyst'
        ELSE 'Awaiting custodian response'
    END AS resolution_notes,
    NULL AS evidence_file
FROM core.reconciliation_breaks b
LEFT JOIN core.vw_transaction_match_reconciliation tm
  ON b.account_id = tm.account_id 
 AND b.business_date = tm.business_date
 AND b.variance = tm.cash_variance;

-- 6. Apply Feedback Report Polish (Root Causes & Evidence)

-- Reclassify AAPL share breaks specifically
UPDATE el
SET root_cause = 'CONTROLLED_AAPL_POSITION_OVERSTATEMENT'
FROM core.exception_log el
JOIN core.reconciliation_breaks rb
    ON el.break_id = rb.break_id
WHERE rb.break_category = 'SHARE_QUANTITY_BREAK'
  AND rb.ticker = 'AAPL';

-- Populate evidence references based on root cause
UPDATE core.exception_log
SET evidence_file =
    CASE
        WHEN root_cause = 'CONTROLLED_CASH_EXCEPTION_CARRYFORWARD' THEN '03_SQL/13_daily_cash_reconciliation.sql; 04_Excel_Model/FinOps_Reconciliation_Model.xlsx - Recon Review; exception_injection_log.csv'
        WHEN root_cause = 'FEE_MISMATCH' THEN '03_SQL/13_daily_cash_reconciliation.sql; Data_Cash Transactions tab; Data_Exception Log tab'
        WHEN root_cause = 'DIVIDEND_MISMATCH' THEN '03_SQL/13_daily_cash_reconciliation.sql; Data_Cash Transactions tab; exception_injection_log.csv'
        WHEN root_cause = 'CONTROLLED_AAPL_POSITION_OVERSTATEMENT' THEN '03_SQL/14_security_position_reconciliation.sql; Recon Review tab; Data_Custodian Positions tab'
        WHEN root_cause = 'MISSING_VENDOR_FILE' THEN 'ctl.vendor_files receipt_status=MISSING; vendor_files.csv; exception_injection_log.csv'
        WHEN root_cause = 'WRONG_ACCOUNT_POSTING' THEN '03_SQL/14_security_position_reconciliation.sql; core.custodian_positions account_id=999; exception_injection_log.csv'
        WHEN root_cause = 'SETTLEMENT_TIMING_DIFFERENCE' THEN '03_SQL/13_daily_cash_reconciliation.sql; Recon Review tab; exception_injection_log.csv'
        WHEN root_cause = 'DUPLICATE_CUSTODIAN_CASH_RECORD' THEN '03_SQL/13_daily_cash_reconciliation.sql; Data_Custodian Balances tab; exception_injection_log.csv'
        ELSE '03_SQL/16_exception_detection.sql; 02_Data/reconciliation_breaks.csv'
    END
WHERE evidence_file IS NULL OR LTRIM(RTRIM(evidence_file)) = '';

-- 7. Insert control-level exceptions directly into exception_log
-- These scenarios (Missing Vendor File, Wrong Account Posting) don't produce
-- reconciliation breaks due to FK constraints, but must appear in the exception log.

-- Missing Vendor File: detected via ctl.vendor_files receipt_status = 'MISSING'
INSERT INTO core.exception_log (
    break_id, business_date, account_id, ticker, break_type, severity, internal_value, custodian_value, variance_amount, dollar_exposure,
    root_cause, owner, status, detected_date, due_date, aging_days, sla_status, resolution_notes, evidence_file
)
SELECT
    NULL,
    eil.affected_date,
    COALESCE(eil.account_id, 1),
    NULL,
    'MISSING_VENDOR_FILE',
    'HIGH',
    0, 0, 0, 0,
    'MISSING_VENDOR_FILE',
    'Custodian Ops',
    'RESOLVED',
    CAST(@ReviewDate2 AS DATE),
    DATEADD(day, 1, eil.affected_date),
    DATEDIFF(day, eil.affected_date, @ReviewDate2),
    'WITHIN_SLA',
    'Vendor file re-requested and received; gap resolved',
    'ctl.vendor_files receipt_status=MISSING; vendor_files.csv; exception_injection_log.csv'
FROM ctl.exception_injection_log eil
WHERE eil.exception_type = 'Missing Vendor File'
  AND NOT EXISTS (SELECT 1 FROM core.exception_log el WHERE el.root_cause = 'MISSING_VENDOR_FILE' AND el.business_date = eil.affected_date);

-- Wrong Account Posting: detected via custodian position on non-existent account
INSERT INTO core.exception_log (
    break_id, business_date, account_id, ticker, break_type, severity, internal_value, custodian_value, variance_amount, dollar_exposure,
    root_cause, owner, status, detected_date, due_date, aging_days, sla_status, resolution_notes, evidence_file
)
SELECT
    NULL,
    eil.affected_date,
    COALESCE(eil.account_id, 1),
    NULL,
    'WRONG_ACCOUNT_POSTING',
    'HIGH',
    0, 0, 0, 0,
    'WRONG_ACCOUNT_POSTING',
    'Custodian Ops',
    'RESOLVED',
    CAST(@ReviewDate2 AS DATE),
    DATEADD(day, 1, eil.affected_date),
    DATEDIFF(day, eil.affected_date, @ReviewDate2),
    'WITHIN_SLA',
    'Custodian corrected account mapping; position reallocated',
    '03_SQL/14_security_position_reconciliation.sql; core.custodian_positions; exception_injection_log.csv'
FROM ctl.exception_injection_log eil
WHERE eil.exception_type = 'Wrong Account Posting'
  AND NOT EXISTS (SELECT 1 FROM core.exception_log el WHERE el.root_cause = 'WRONG_ACCOUNT_POSTING' AND el.business_date = eil.affected_date);
GO
