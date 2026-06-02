CREATE OR ALTER VIEW rpt.vw_injection_validation AS
WITH detected_breaks AS (
    SELECT
        injection_id,
        COUNT(*) AS detected_break_count,
        SUM(ABS(COALESCE(cash_variance, 0))) AS cumulative_detected_exposure
    FROM core.vw_daily_cash_reconciliation
    WHERE injection_id IS NOT NULL
      AND break_type <> 'MATCHED'
    GROUP BY injection_id

    UNION ALL

    SELECT
        injection_id,
        COUNT(*) AS detected_break_count,
        CAST(0 AS decimal(19,4)) AS cumulative_detected_exposure
    FROM core.vw_security_position_reconciliation
    WHERE injection_id IS NOT NULL
      AND break_type <> 'MATCHED'
    GROUP BY injection_id
),
summarized AS (
    SELECT
        injection_id,
        SUM(detected_break_count) AS detected_break_count,
        SUM(cumulative_detected_exposure) AS cumulative_detected_exposure
    FROM detected_breaks
    GROUP BY injection_id
)
SELECT
    inj.injection_id,
    inj.exception_type,
    inj.expected_detection_rule,
    COALESCE(s.detected_break_count, 0) AS detected_break_count,
    COALESCE(s.cumulative_detected_exposure, 0) AS cumulative_detected_exposure,
    CASE
        WHEN COALESCE(s.detected_break_count, 0) > 0 THEN 'DETECTED'
        ELSE 'NOT_DETECTED'
    END AS detection_status
FROM ctl.exception_injection_log inj
LEFT JOIN summarized s
    ON inj.injection_id = s.injection_id;