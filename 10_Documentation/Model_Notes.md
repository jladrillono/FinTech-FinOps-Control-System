# FinOps Reconciliation Model — Notes

## Purpose
This Excel workbook is the operational review layer for the FinOps Reconciliation System. It provides management dashboards, reconciliation validation, exception aging analysis, and control documentation — all generated programmatically from the SQL Server backend.

## Data Sources
- **Database**: SQL Server `FinOps_Control_System`
- **Schema**: `core.*` (operational tables), `ctl.*` (control/vendor tables), `rpt.*` (reporting views)
- **Validation CSVs**: `02_Data/injection_to_break_validation.csv`, `02_Data/ledger_rollforward_validation.csv`

## Refresh Sequence
1. `rebuild_pipeline.ps1` — Drops/rebuilds all tables, loads synthetic data, runs reconciliation, exports CSVs
2. `06_Python/build_excel_model.py` — Reads live SQL data + validation CSVs, generates `FinOps_Reconciliation_Model.xlsx`

**Never manually edit data tabs.** All values are overwritten on each rebuild.

## Tab Map
| Tab | Purpose |
|-----|---------|
| Instructions | Workbook documentation, tab map, formulas, limitations |
| Dashboard | 12 KPIs, 4 charts (root cause pie, exposure bar, owner pie, status pie) |
| Tie-Outs | 15 validation checks with PASS/FAIL conditional formatting |
| Exception Aging | SLA/severity/root cause summary, aging buckets, open by owner, root cause x status |
| Control Summary | 10 controls with 12 fields: ID, name, area, risk, activity, frequency, owner, evidence, status, exception handling, review date, related output |
| Recon Review | Formula-driven sandbox: `=IFERROR(ROUND(C-F, 2), "Review")` comparing internal vs custodian cash |
| Validation_Injections | 8 injected exception scenarios with DETECTED/NOT DETECTED status |
| Validation_Ledger | Ledger roll-forward results (0 rows = PASS) |
| Data_* tabs | Raw SQL table exports as Excel Tables |

## Key Formulas
- **Total Exceptions**: `=COUNTA(tbl_exception_log[exception_id])` — uses `exception_id` (not `break_id`) to include control-level exceptions with NULL `break_id`
- **Recon Variance**: `=IFERROR(ROUND(C{row}-F{row}, 2), "Review")` — C = `cash_balance`, F = `custodian_cash_balance`
- **Pass/Fail**: `=IF(ABS(G{row})>0.01, "Break", "Pass")`

## Validation Checks (Tie-Outs Tab)
Row counts, exposure totals, injection detection, evidence completeness, and break category counts are all validated with PASS/FAIL status.

## Known Limitations
- **Simulated data**: Custodian records are synthetically generated from internal ledger data with 8 controlled exception injections
- **Dollar exposure proxy**: Share breaks use $150/share multiplier (no live price feed)
- **Fixed review date**: All aging/SLA calculations use `2024-07-05` as the simulated review date
- **Status assignment**: Exception statuses (OPEN/IN_REVIEW/PENDING_VENDOR/RESOLVED) are distributed via modular arithmetic on `break_id` for variety, not based on actual workflow
