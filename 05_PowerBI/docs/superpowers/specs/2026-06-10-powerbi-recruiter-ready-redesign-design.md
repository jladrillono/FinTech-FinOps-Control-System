# Power BI Recruiter-Ready Redesign Design

## Purpose

Redesign the `Dimensions Financial Operations Dashboard` as a recruiter-ready Power BI portfolio deliverable for fintech financial operations, reconciliation, controls, and reporting roles. The dashboard must answer management questions quickly, use reliable KPI measures, expose validation evidence, and avoid claims that imply live production reporting or regulatory certification.

## Source Requirements

The design is based on `PowerBI_Dashboard_Redesign_Project_Instructions.pdf`, the current `Dimensions Financial Operations Dashboard.pbip` and `.pbix`, the PBIR report source under `Dimensions Financial Operations Dashboard.Report`, and the existing documentation and validation assets in `05_PowerBI`.

The implementation will keep the current semantic model and source logic intact. It will not rebuild SQL logic, Excel formulas, Python scripts, or reconciliation rules. If any measure or field cannot be tied out during implementation, the dashboard and validation documentation will label it as Power BI-only supporting analysis or a known validation limitation.

## Recommended Approach

Use Option A: Recruiter-Ready Redesign. This keeps the current working page set and model, but improves page storytelling, visual choices, theme consistency, validation evidence, and documentation packaging. This avoids a broad rebuild while addressing the assignment's required deliverables.

## Page Architecture

The final navigation should tell a management story in this order:

1. Executive Overview - Is the overall process under control?
2. Exception Management - Which breaks need action first?
3. Cash Monitoring - Which accounts show unusual cash behavior?
4. Security Reconciliation - Where do internal and custodian security positions not match?
5. Controls and Audit Readiness - Are controls working and is evidence ready?
6. Validation Appendix - Do Power BI measures tie to SQL and Excel outputs?
7. Python Validation and Anomaly Monitoring - What did automated checks flag for review?
8. Model QA Appendix - Is the model technically reliable?

The Model QA page should be hidden from recruiter-facing navigation if Power BI metadata supports that cleanly. If hiding is not reliable in the PBIR source, it should be renamed or documented as a technical appendix and placed at the end of the page order.

## Page-Level Redesign

Executive Overview will remove or de-emphasize redundant count cards and move Detection Rate to validation. It should keep a compact KPI strip for total activity, open exceptions, over-SLA workload, unresolved dollar exposure, and control pass rate. It should replace donut-style status comparison with a more readable status or root-cause bar visual and include a top action priority table when fields are available.

Exception Management will prioritize action. It should retain action KPIs for open, over-SLA, due-soon, high-severity, and unresolved exposure. Weak owner/status visuals should be replaced or retitled when they do not support prioritization. The page should emphasize aging bucket, SLA pressure, root cause by unresolved exposure, break type, severity, owner, and review action.

Cash Monitoring will focus on unusual account behavior. It should reduce broad transaction-mix visuals that do not identify reconciliation risk. It should emphasize negative balance count, excess balance count, top cash variance accounts, cash roll-forward or variance trend, and detail review by account.

Security Reconciliation will focus on account and ticker mismatches. It should avoid aggregate share comparisons that hide account-level breaks. It should emphasize top security breaks by exposure, share variance by account or ticker, security break type mix, and position mismatch detail.

Controls and Audit Readiness will connect controls to process risk. It should show pass/fail by process area, evidence readiness by record type or process area, controls with open exceptions, cadence or owner accountability, and books-and-records summary indicators.

Validation Appendix will prove KPI reliability. It should include a KPI validation scorecard and a validation findings table with Power BI value, SQL value, Excel value, variance, status, color code, and notes. Donut charts used for exposure/category comparison should be replaced with sorted bars.

Python Validation and Anomaly Monitoring will show automated review findings. Vendor issue visuals must use true issue counts when available. The page should show failed checks by check type or source file, vendor file validation status, anomaly count by type and severity, and high-risk anomaly detail.

## Color System

Use one consistent FinOps palette across the theme, page headers, cards, bars, tables, slicers, and validation artifacts.

| Purpose | Name | Hex |
| --- | --- | --- |
| Header and primary text | Navy | `#0B1F33` |
| Primary measures | Blue | `#2563EB` |
| Secondary analysis | Teal | `#14B8A6` |
| Warning and SLA pressure | Amber | `#F59E0B` |
| Failed or high risk | Red | `#DC2626` |
| Passed or healthy | Green | `#16A34A` |
| Page background | Off-white | `#F8FAFC` |
| Visual background | White | `#FFFFFF` |
| Borders and dividers | Light gray | `#D9E2EC` |
| Muted labels | Slate gray | `#64748B` |

Red, amber, and green should be reserved for severity, SLA, pass/fail, and action status. Category colors should use blue, teal, navy, and muted variants before using status colors.

## Data and Validation

Core KPI cards must use documented measures or clearly documented field aggregations. The validation checklist should cover at least Total Transactions, Accounts Reviewed, Open Exceptions, Breaks Over SLA, Dollar Exposure, Control Pass Rate, Average Exception Age when available, and Injection Detection Rate.

The validation artifact should include:

- `kpi_name`
- `power_bi_source`
- `power_bi_value`
- `sql_source`
- `sql_value`
- `excel_source`
- `excel_value`
- `variance`
- `status`
- `status_color_hex`
- `notes`

Status color values should use `#16A34A` for pass, `#F59E0B` for warning, and `#DC2626` for fail.

## Files and Deliverables

The implementation should modify or create:

- PBIR report source under `Dimensions Financial Operations Dashboard.Report`
- Theme files under `Dimensions Financial Operations Dashboard.Report/StaticResources`
- `Dashboard_Visual_Review_Log.md`
- `kpi_validation_checklist.md`
- `Dashboard_Notes.md`
- `README.md`
- `Progress_Log.md`
- `Change_Log.md`
- Optional generated inventory or validation outputs under an `outputs` folder if useful

The existing `.pbix` should be opened and saved through Power BI Desktop if Computer Use can access the app successfully. If Power BI Desktop cannot open or save the report in this environment, the PBIR package and documentation updates remain the source-controlled deliverable, and the limitation must be documented.

## Testing and Verification

Verification should include JSON parsing for all edited PBIR and theme files, PowerShell validation scripts in `tests`, a KPI validation artifact review, and a Computer Use visual smoke test in Power BI Desktop if available. The final report should have no misleading titles, no donut charts where precise category comparison is the main task, and no main navigation page that presents Model QA as a recruiter-facing management page.

## Documentation Rules

Documentation must frame the dashboard as a simulated portfolio deliverable. It must avoid live customer data, live brokerage system, production reporting, regulatory certification, or actual compliance evidence claims. It should explain sources, relationships, DAX measures, validation checks, assumptions, limitations, and known unresolved issues in recruiter-readable language.
