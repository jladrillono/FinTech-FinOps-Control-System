-- ==============================================================================
-- Script: 11_exception_injection.sql
-- Purpose: Injects controlled exceptions into the custodian simulation tables.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- Variables for injection tracking
DECLARE @InjId INT;

-- ---------------------------------------------------------
-- EXCEPTION 1: Missing Cash Record (Simulated via Deletion)
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, impact_amount, expected_detection_rule, resolution_expectation)
VALUES ('Missing Cash Record', 'core.custodian_balances', 1, '2021-01-04', 'Vendor file dropped a row', -1000.00, 'Cash Balance Variance', 'Vendor to re-send file');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_balances
SET custodian_cash_balance = custodian_cash_balance - 1000.00,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 1 AND balance_date >= '2021-01-04';

-- ---------------------------------------------------------
-- EXCEPTION 2: Fee Mismatch (Amount Difference)
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, impact_amount, expected_detection_rule, resolution_expectation)
VALUES ('Fee Mismatch', 'core.custodian_balances', 2, '2021-02-15', 'Custodian applied different fee schedule', -2.50, 'Small Cash Variance', 'Reconcile and accept as operational loss');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_balances
SET custodian_cash_balance = custodian_cash_balance - 2.50,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 2 AND balance_date >= '2021-02-15';

-- ---------------------------------------------------------
-- EXCEPTION 3: Settlement Timing Difference
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, impact_amount, expected_detection_rule, resolution_expectation)
VALUES ('Timing Difference', 'core.custodian_balances', 3, '2021-03-10', 'T+1 Settlement delay on custodian side', -500.00, 'Timing Break', 'Will clear automatically on T+1');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_balances
SET custodian_cash_balance = custodian_cash_balance - 500.00,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 3 AND balance_date = '2021-03-10';

-- ---------------------------------------------------------
-- EXCEPTION 4: Share Quantity Mismatch
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, ticker, affected_date, root_cause, impact_shares, expected_detection_rule, resolution_expectation)
VALUES ('Share Mismatch', 'core.custodian_positions', 4, 'AAPL', '2021-06-01', 'Corporate action not processed internally', 10.0000, 'Security Position Break', 'Operations to book corporate action');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_positions
SET custodian_share_quantity = custodian_share_quantity + 10.0000,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 4 AND ticker = 'AAPL' AND position_date >= '2021-06-01';

-- ---------------------------------------------------------
-- EXCEPTION 5: Duplicate Cash Record
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, impact_amount, expected_detection_rule, resolution_expectation)
VALUES ('Duplicate Cash Record', 'core.custodian_balances', 5, '2021-08-20', 'Custodian sent file twice or duplicated row', 250.00, 'Unexplained Cash Variance', 'Reverse duplicate entry');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_balances
SET custodian_cash_balance = custodian_cash_balance + 250.00,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 5 AND balance_date >= '2021-08-20';

-- ---------------------------------------------------------
-- EXCEPTION 6: Missing Vendor File
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, affected_date, root_cause, expected_detection_rule, resolution_expectation)
VALUES ('Missing Vendor File', 'ctl.vendor_files', '2021-09-01', 'SFTP connection failed', 'File Completeness Control', 'Retry SFTP connection');
SET @InjId = SCOPE_IDENTITY();

UPDATE ctl.vendor_files
SET receipt_status = 'MISSING',
    validation_status = 'FAILED',
    received_timestamp = NULL
WHERE expected_date = '2021-09-01' AND file_name LIKE 'CUST_POS_%';

-- ---------------------------------------------------------
-- EXCEPTION 7: Dividend Mismatch
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, impact_amount, expected_detection_rule, resolution_expectation)
VALUES ('Dividend Mismatch', 'core.custodian_balances', 6, '2022-01-15', 'Tax withholding applied differently', -15.50, 'Income Variance', 'Review tax logic');
SET @InjId = SCOPE_IDENTITY();

UPDATE core.custodian_balances
SET custodian_cash_balance = custodian_cash_balance - 15.50,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 6 AND balance_date >= '2022-01-15';

-- ---------------------------------------------------------
-- EXCEPTION 8: Wrong Account Posting
-- ---------------------------------------------------------
INSERT INTO ctl.exception_injection_log (exception_type, affected_table, account_id, affected_date, root_cause, expected_detection_rule, resolution_expectation)
VALUES ('Wrong Account Posting', 'core.custodian_positions', 7, '2022-05-05', 'Custodian mapped ticker to wrong sub-account', 'Offsetting Security Break across accounts', 'Submit correction to custodian');
SET @InjId = SCOPE_IDENTITY();

-- Insert dummy position into a fake account
INSERT INTO core.custodian_positions (source_file_id, account_id, position_date, ticker, custodian_share_quantity, simulation_flag, injection_id)
SELECT TOP 1 source_file_id, 999, position_date, 'MSFT', 50.0000, 'INJECTED', @InjId
FROM core.custodian_positions
WHERE position_date = '2022-05-05';

-- Remove it from the real account (account_id = 7)
UPDATE core.custodian_positions
SET custodian_share_quantity = custodian_share_quantity - 50.0000,
    simulation_flag = 'INJECTED',
    injection_id = @InjId
WHERE account_id = 7 AND ticker = 'MSFT' AND position_date >= '2022-05-05';
GO
