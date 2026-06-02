INSERT INTO ctl.books_records_index
(
    record_type,
    retention_logic,
    evidence_location,
    worm_compliant
)
SELECT *
FROM
(
    VALUES
    ('Raw Transaction File',
     'Retain source transaction file to support traceability from raw data to transformed outputs.',
     '02_Data/raw_stock_transactions.csv',
     1),

    ('Data Dictionary',
     'Retain field definitions, data types, business rules, and validation notes for methodology support.',
     '02_Data/data_dictionary.csv',
     1),

    ('Transaction Type Mapping',
     'Retain transaction classification rules used to assign cash and security impacts.',
     '02_Data/transaction_type_mapping.csv',
     1),

    ('SQL Schema Scripts',
     'Retain database structure, table definitions, keys, schemas, and control table design.',
     '03_SQL/schema.sql',
     1),

    ('SQL Transformation Scripts',
     'Retain transformation logic that converts raw records into cleaned financial operations tables.',
     '03_SQL/transformations.sql',
     1),

    ('Internal Ledger Output',
     'Retain calculated cash ledger balances used as the internal system of record for reconciliation.',
     '02_Data/internal_ledger.csv',
     1),

    ('Security Positions Output',
     'Retain calculated account and ticker-level security positions used for custodian comparison.',
     '02_Data/positions.csv',
     1),

    ('Custodian Balance File',
     'Retain simulated external balance records used to test reconciliation logic.',
     '02_Data/custodian_balances.csv',
     1),

    ('Custodian Position File',
     'Retain simulated external position records used to test share quantity reconciliation.',
     '02_Data/custodian_positions.csv',
     1),

    ('Reconciliation Breaks Output',
     'Retain detected cash, security, transaction, timing, duplicate, and missing-record breaks.',
     '02_Data/reconciliation_breaks.csv',
     1),

    ('Exception Log',
     'Retain operational exception tracker with root cause, owner, SLA, aging, status, and exposure.',
     '02_Data/exception_log.csv',
     1),

    ('Excel Reconciliation Model',
     'Retain manual review workbook used to validate SQL outputs and summarize exceptions.',
     '04_Excel_Model/FinOps_Reconciliation_Model.xlsx',
     1),

    ('Power BI Dashboard',
     'Retain management dashboard file showing KPIs, exceptions, controls, and operational risk.',
     '05_PowerBI/FinOps_Dashboard.pbix',
     1),

    ('Python Validation Outputs',
     'Retain automated validation and anomaly detection outputs used for control support.',
     '06_Python/outputs/python_validation_summary.csv',
     1),

    ('Control Matrix',
     'Retain risk-control mapping showing control activities, ownership, frequency, and evidence.',
     '07_Control_Documentation/Control_Matrix.xlsx',
     1),

    ('Procedure Document',
     'Retain process documentation explaining data intake, reconciliation, exception handling, and reporting.',
     '07_Control_Documentation/Procedure_Document.docx',
     1),

    ('Monthly FinOps Summary',
     'Retain management-ready summary of reconciliation results, root causes, risks, and recommended actions.',
     '08_Executive_Output/Monthly_FinOps_Summary.docx',
     1),

    ('README Documentation',
     'Retain recruiter-facing project explanation, workflow, tools, screenshots, limitations, and project value.',
     'README.md',
     1)
) AS v
(
    record_type,
    retention_logic,
    evidence_location,
    worm_compliant
)
WHERE NOT EXISTS
(
    SELECT 1
    FROM ctl.books_records_index bri
    WHERE bri.record_type = v.record_type
      AND bri.evidence_location = v.evidence_location
);