-- ==============================================================================
-- Script: 10_custodian_simulation.sql
-- Purpose: Creates the baseline simulated external custodian records.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Clear previous simulation runs
TRUNCATE TABLE core.custodian_balances;
TRUNCATE TABLE core.custodian_positions;

-- Clear downstream tables that have FKs to ctl.vendor_files or ctl.exception_injection_log
DELETE FROM core.exception_log;
DBCC CHECKIDENT ('core.exception_log', RESEED, 0);
DELETE FROM core.reconciliation_breaks;
DBCC CHECKIDENT ('core.reconciliation_breaks', RESEED, 0);

DELETE FROM ctl.vendor_files;
DBCC CHECKIDENT ('ctl.vendor_files', RESEED, 0);
DELETE FROM ctl.exception_injection_log;
DBCC CHECKIDENT ('ctl.exception_injection_log', RESEED, 0);
GO

-- 2. Generate Vendor File Receipts
-- We simulate receiving one balance file and one position file per day
INSERT INTO ctl.vendor_files (file_name, source_system, expected_date, receipt_status, received_timestamp, validation_status)
SELECT DISTINCT 
    'CUST_BAL_' + FORMAT(ledger_date, 'yyyyMMdd') + '.csv',
    'Custodian_Bank',
    ledger_date,
    'RECEIVED',
    DATEADD(hour, 6, CAST(ledger_date AS DATETIME2)), -- Simulated 6 AM receipt
    'VALIDATED'
FROM core.internal_ledger_balances;

INSERT INTO ctl.vendor_files (file_name, source_system, expected_date, receipt_status, received_timestamp, validation_status)
SELECT DISTINCT 
    'CUST_POS_' + FORMAT(position_date, 'yyyyMMdd') + '.csv',
    'Custodian_Bank',
    position_date,
    'RECEIVED',
    DATEADD(hour, 6, CAST(position_date AS DATETIME2)),
    'VALIDATED'
FROM core.positions;
GO

-- 3. Populate Baseline Custodian Balances
-- Matches internal ledger exactly before any exceptions are injected
INSERT INTO core.custodian_balances (
    source_file_id, account_id, balance_date, custodian_cash_balance, currency, record_status, simulation_flag
)
SELECT 
    v.source_file_id,
    l.account_id,
    l.ledger_date,
    l.cash_balance,
    'GBP',
    'BASELINE',
    'CLEAN'
FROM core.internal_ledger_balances l
JOIN ctl.vendor_files v 
  ON v.expected_date = l.ledger_date 
 AND v.file_name LIKE 'CUST_BAL_%';
GO

-- 4. Populate Baseline Custodian Positions
-- Matches internal positions exactly before exceptions
INSERT INTO core.custodian_positions (
    source_file_id, account_id, position_date, ticker, isin, custodian_share_quantity, simulation_flag
)
SELECT 
    v.source_file_id,
    p.account_id,
    p.position_date,
    p.ticker,
    NULL, -- Missing ISIN to simulate messy vendor data
    p.share_quantity,
    'CLEAN'
FROM core.positions p
JOIN ctl.vendor_files v 
  ON v.expected_date = p.position_date 
 AND v.file_name LIKE 'CUST_POS_%';
GO

-- 5. Update Vendor File Control Totals
-- Simulates the vendor file header counts/totals
UPDATE v
SET v.record_count = c.RowCnt,
    v.control_total = c.TotalAmount
FROM ctl.vendor_files v
JOIN (
    SELECT source_file_id, COUNT(*) AS RowCnt, SUM(custodian_cash_balance) AS TotalAmount
    FROM core.custodian_balances
    GROUP BY source_file_id
) c ON v.source_file_id = c.source_file_id
WHERE v.file_name LIKE 'CUST_BAL_%';

UPDATE v
SET v.record_count = c.RowCnt,
    v.control_total = c.TotalShares
FROM ctl.vendor_files v
JOIN (
    SELECT source_file_id, COUNT(*) AS RowCnt, SUM(custodian_share_quantity) AS TotalShares
    FROM core.custodian_positions
    GROUP BY source_file_id
) c ON v.source_file_id = c.source_file_id
WHERE v.file_name LIKE 'CUST_POS_%';
GO
