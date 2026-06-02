-- ==============================================================================
-- Script: 17_phase5_validation_checks.sql
-- Purpose: Validates that Phase 5 detected the controlled exceptions.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Total Breaks Detected
SELECT 
    'Total Breaks Detected' AS CheckName,
    COUNT(*) AS BreakCount
FROM core.reconciliation_breaks;

-- 2. Root Cause Classification Check
SELECT 
    'Root Cause Breakdown' AS CheckName,
    root_cause,
    COUNT(*) AS BreakCount
FROM core.exception_log
GROUP BY root_cause
ORDER BY BreakCount DESC;

-- 3. Injected Exception Coverage (Did we detect the Phase 4 injections?)
-- We injected 8 exceptions on specific dates. Let's see if we caught them.
SELECT 
    'Injected Exception Coverage' AS CheckName,
    i.exception_type AS InjectedType,
    i.affected_date,
    COUNT(e.exception_id) AS DetectedCount,
    CASE WHEN COUNT(e.exception_id) > 0 THEN 'DETECTED' ELSE 'MISSED' END AS Status
FROM ctl.exception_injection_log i
LEFT JOIN core.exception_log e 
  ON (i.affected_date = e.business_date)
GROUP BY i.exception_type, i.affected_date
ORDER BY i.affected_date;

-- 4. Null Critical Fields Check
SELECT 
    'Null Critical Fields' AS CheckName,
    SUM(CASE WHEN break_type IS NULL THEN 1 ELSE 0 END) AS NullType,
    SUM(CASE WHEN root_cause IS NULL THEN 1 ELSE 0 END) AS NullCause,
    SUM(CASE WHEN severity IS NULL THEN 1 ELSE 0 END) AS NullSeverity,
    SUM(CASE WHEN dollar_exposure IS NULL THEN 1 ELSE 0 END) AS NullExposure
FROM core.exception_log;
GO
