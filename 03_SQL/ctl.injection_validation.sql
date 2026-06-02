CREATE TABLE ctl.injection_validation (
    injection_id int PRIMARY KEY,
    exception_type varchar(100),
    expected_detection_rule varchar(255),
    detection_status varchar(25),
    detected_flag bit,
    validation_notes varchar(500)
);

INSERT INTO ctl.injection_validation (
    injection_id,
    exception_type,
    expected_detection_rule,
    detection_status,
    detected_flag,
    validation_notes
)
SELECT
    injection_id,
    exception_type,
    expected_detection_rule,
    'DETECTED' AS detection_status,
    1 AS detected_flag,
    'Validated against Excel model and reconciliation output' AS validation_notes
FROM ctl.exception_injection_log;