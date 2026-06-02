-- ==============================================================================
-- Script: 12_phase4_validation_checks.sql
-- Purpose: Validates the simulation and exception injection.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Baseline vs Custodian Record Counts
SELECT 
    'Cash Record Count' AS CheckName,
    (SELECT COUNT(*) FROM core.internal_ledger_balances) AS InternalCount,
    (SELECT COUNT(*) FROM core.custodian_balances) AS CustodianCount;

SELECT 
    'Position Record Count' AS CheckName,
    (SELECT COUNT(*) FROM core.positions) AS InternalCount,
    (SELECT COUNT(*) FROM core.custodian_positions) AS CustodianCount;

-- 2. Injection Log Count vs Planned
SELECT 
    'Injection Log Count' AS CheckName,
    COUNT(*) AS ActualInjections,
    8 AS PlannedInjections,
    CASE WHEN COUNT(*) = 8 THEN 'PASS' ELSE 'FAIL' END AS Status
FROM ctl.exception_injection_log;

-- 3. Affected Records Count
SELECT 
    'Modified Cash Records' AS CheckName,
    COUNT(*) AS ModifiedCount
FROM core.custodian_balances
WHERE simulation_flag = 'INJECTED';

SELECT 
    'Modified Position Records' AS CheckName,
    COUNT(*) AS ModifiedCount
FROM core.custodian_positions
WHERE simulation_flag = 'INJECTED';

-- 4. Missing File Check
SELECT 
    'Missing Files' AS CheckName,
    COUNT(*) AS MissingCount
FROM ctl.vendor_files
WHERE receipt_status = 'MISSING';

-- 5. Linkage Check (No orphans)
SELECT 
    'Orphan Injections' AS CheckName,
    COUNT(*) AS OrphanCount
FROM core.custodian_balances
WHERE simulation_flag = 'INJECTED' AND injection_id IS NULL;
GO
