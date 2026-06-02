# Change Log

## Version: v1.8
**Date:** May 17, 2026
**Change:** Completed Phase 8 Python Validation and Anomaly Monitoring. Built four Python scripts — `anomaly_detection.py`, `data_quality_checks.py`, `vendor_file_validation.py`, and `run_all_validations.py` — to automate data quality testing, vendor file verification, and anomaly flagging. Outputs integrated into Power BI dashboard.
**Impact:** Adds an automated validation layer that identifies negative balances, statistical outliers, vendor file gaps, duplicate records, and high-risk anomaly concentrations. Strengthens the reconciliation workflow by surfacing issues before management relies on dashboard outputs.


## Version: v1.7
**Date:** May 17, 2026
**Change:** Completed Phase 7 Power BI Dashboard. Built a 7-page executive dashboard covering operational overview, cash monitoring, security reconciliation, exception management, controls, validation, and Python anomaly monitoring.
**Impact:** Converts reconciliation and exception outputs into executive-ready visual reporting. Provides management with clear visibility into operational status, unresolved risk, aging exceptions, root-cause patterns, and control performance.


## Version: v1.6
**Date:** May 16, 2026
**Change:** Completed Phase 6 Excel Model. Built Python pipeline (`build_excel_model.py`) utilizing `xlsxwriter` to natively generate the `FinOps_Reconciliation_Model.xlsx`. The model successfully features management dashboards, pie charts, formula-driven sandbox tabs, conditional formatting, and control tie-outs.
**Impact:** Converts raw SQL variance tables into a transparent, recruiter-ready manual review layer. Proves end-to-end data pipeline competency spanning SQL analytics to operational spreadsheet automation.


## Version: v1.5
**Date:** May 16, 2026
**Change:** Completed Phase 5 Reconciliation and Exceptions. Updated schema to expand tracking fields. Implemented 5 SQL scripts (views and stored procedures equivalents) to automate the variance detection between internal and external records.
**Impact:** The system can now automatically catch operational breaks, assign SLAs, calculate dollar exposures, and log root causes. Proven to detect 100% of injected errors.


## Version: v1.4
**Date:** May 16, 2026
**Change:** Completed Phase 4 Custodian Simulation and Exception Injection. Rebuilt schema to include `ctl.vendor_files`, `ctl.exception_injection_log`, and `core.custodian_*` tables. Exported simulation data to CSV format.
**Impact:** Established the simulated external data source. By intentionally injecting 8 controlled errors, the project now has a robust testing ground for the Phase 5 automated reconciliation logic.


## Version: v1.3
**Date:** May 16, 2026
**Change:** Completed Phase 3 Ledger and Position Roll-Forward logic. Added `08_ledger_balances.sql` and `09_security_positions.sql` to generate continuous daily snapshot balances from point-in-time transactions.
**Impact:** Enables direct day-to-day reconciliation against external custodian records by ensuring every account/ticker has an ending balance for every calendar day, even on days with zero activity.


## Version: v1.2
**Date:** May 16, 2026
**Change:** Completed Phase 2 SQL Data Model. Generated schema, staging, transformation, and reporting views. Documented methodology, runbook, and simulated execution.
**Impact:** Provides an auditable data flow to transition from raw data into operational facts, setting the foundation for the Phase 3 balance calculations and downstream reconciliation.

## Version: v1.1
**Date:** May 16, 2026
**Change:** Added Phase 1 Data Understanding deliverables and formalized raw dataset review, transaction mapping, and data quality requirements. Extracted base dataset to `raw_stock_transactions.csv`.
**Impact:** Creates a documented foundation for SQL schema development and reduces the risk of inconsistent transaction logic in later phases by standardizing cash and security impact definitions early.
