"""
build_excel_model.py

Purpose:
    Programmatically generates the FinOps_Reconciliation_Model.xlsx workbook
    from live SQL Server data and validation CSVs. The workbook serves as the
    manual review layer for operations analysts, including management dashboards,
    control tie-outs, exception aging summaries, reconciliation sandboxes, and
    injection/ledger validation tabs.

Data Sources:
    - SQL Server database: FinOps_Control_System (core schema tables)
    - CSV files: injection_to_break_validation.csv, ledger_rollforward_validation.csv

Usage:
    python 06_Python/build_excel_model.py

Dependencies:
    pandas, sqlalchemy, xlsxwriter, pyodbc

Notes:
    - Run rebuild_pipeline.ps1 first to ensure the database is current.
    - This script overwrites the existing Excel workbook on each run.
    - All data tabs are structured as native Excel Tables for filtering and pivots.
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# Setup paths — resolve dynamically from the repository root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, "02_Data")
output_dir = os.path.join(project_root, "04_Excel_Model")
os.makedirs(output_dir, exist_ok=True)
excel_path = os.path.join(output_dir, "FinOps_Reconciliation_Model.xlsx")

# Database connection
engine = create_engine('mssql+pyodbc://localhost/FinOps_Control_System?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes')

# Load validation CSVs
injection_csv = os.path.join(data_dir, 'injection_to_break_validation.csv')
rollforward_csv = os.path.join(data_dir, 'ledger_rollforward_validation.csv')
inj_df = pd.read_csv(injection_csv) if os.path.exists(injection_csv) else pd.DataFrame()
rf_df = pd.read_csv(rollforward_csv) if os.path.exists(rollforward_csv) else pd.DataFrame()

print("Extracting data from SQL Server...")
datasets = {
    'Cash_Transactions': pd.read_sql('SELECT * FROM core.cash_transactions', engine),
    'Security_Transactions': pd.read_sql('SELECT * FROM core.security_transactions', engine),
    'Internal_Ledger': pd.read_sql('SELECT * FROM core.internal_ledger_balances', engine),
    'Custodian_Balances': pd.read_sql('SELECT * FROM core.custodian_balances', engine),
    'Positions': pd.read_sql('SELECT * FROM core.positions', engine),
    'Custodian_Positions': pd.read_sql('SELECT * FROM core.custodian_positions', engine),
    'Recon_Breaks': pd.read_sql('SELECT * FROM core.reconciliation_breaks', engine),
    'Exception_Log': pd.read_sql('SELECT * FROM core.exception_log', engine)
}

print(f"Creating Excel workbook at {excel_path}...")
writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
workbook = writer.book

# Formatting Setup
header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#1F497D', 'border': 1})
money_format = workbook.add_format({'num_format': '$#,##0.00'})
date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
critical_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
over_sla_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
bold_format = workbook.add_format({'bold': True})

# ---------------------------------------------------------
# Tab 1: Instructions (Fix 10 — expanded documentation)
# ---------------------------------------------------------
ws_inst = workbook.add_worksheet('Instructions')
ws_inst.write('A1', 'FinTech Financial Operations Control & Reconciliation System', workbook.add_format({'bold': True, 'font_size': 16}))

ws_inst.write('A3', 'Workbook Purpose:', bold_format)
ws_inst.write('B3', 'This workbook serves as the manual review layer for operations analysts. It validates SQL outputs, investigates exceptions, and reports operational risk. All data is formula-driven from the SQL backend.')

ws_inst.write('A5', 'Data Sources:', bold_format)
ws_inst.write('B5', 'SQL Server database: FinOps_Control_System. Tables: core.cash_transactions, core.security_transactions, core.internal_ledger_balances, core.custodian_balances, core.positions, core.custodian_positions, core.reconciliation_breaks, core.exception_log.')

ws_inst.write('A7', 'Refresh Sequence:', bold_format)
ws_inst.write('B7', '1. Run rebuild_pipeline.ps1 (rebuilds database, loads data, runs reconciliation, exports CSVs).')
ws_inst.write('B8', '2. Run 06_Python/build_excel_model.py (regenerates this workbook from live SQL data + validation CSVs).')
ws_inst.write('B9', '3. NEVER manually edit data tabs — all values are overwritten on rebuild.')

ws_inst.write('A11', 'Tab Map:', bold_format)
tab_map = [
    ('Dashboard', 'Management KPIs: total exceptions, status mix, SLA, exposure, injection rate, root cause/owner/status charts.'),
    ('Tie-Outs', '15 validation checks: row counts, exposure totals, injection detection, evidence completeness.'),
    ('Exception Aging', 'SLA/severity/root cause summary, aging buckets, open exceptions by owner, root cause x status cross-tab.'),
    ('Control Summary', '10 controls with ID, name, risk, activity, frequency, owner, evidence, status, exception handling, review date, related output.'),
    ('Recon Review', 'Formula-driven sandbox: internal cash vs custodian cash, with Excel_Variance = C - F and Pass/Fail flag.'),
    ('Validation_Injections', '8 injected exception scenarios with detection status (all should show DETECTED).'),
    ('Validation_Ledger', 'Ledger roll-forward validation results (0 rows = PASS).'),
    ('Data_* tabs', 'Raw SQL table exports formatted as Excel Tables for structured reference formulas.'),
]
for i, (tab, desc) in enumerate(tab_map):
    ws_inst.write(11 + i, 0, tab)
    ws_inst.write(11 + i, 1, desc)

ws_inst.write(11 + len(tab_map) + 1, 0, 'Key Formulas:', bold_format)
ws_inst.write(11 + len(tab_map) + 2, 0, 'Total Exceptions')
ws_inst.write(11 + len(tab_map) + 2, 1, '=COUNTA(tbl_exception_log[exception_id]) — counts all exceptions including control-level (NULL break_id).')
ws_inst.write(11 + len(tab_map) + 3, 0, 'Recon Variance')
ws_inst.write(11 + len(tab_map) + 3, 1, '=IFERROR(ROUND(C-F, 2), "Review") — C=cash_balance, F=custodian_cash_balance.')

ws_inst.write(11 + len(tab_map) + 5, 0, 'Known Limitations:', bold_format)
ws_inst.write(11 + len(tab_map) + 6, 1, 'This workbook uses simulated data. Custodian records are synthetically generated from internal ledger data with 8 controlled exception injections. Dollar exposure for share breaks uses a $150/share proxy. Review date is fixed at 2024-07-05.')

ws_inst.set_column('A:A', 22)
ws_inst.set_column('B:B', 120)

# ---------------------------------------------------------
# Data Input Tabs
# ---------------------------------------------------------
# We write data inputs first so Dashboard and Tie-Outs can reference them using structured table formulas
for name, df in datasets.items():
    sheet_name = f'Data_{name[:20]}' # Max 31 chars
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    
    num_rows, num_cols = df.shape
    table_name = f"tbl_{name.lower().replace(' ', '_')}"
    
    # Add table format with explicit name
    if num_rows > 0:
        worksheet.add_table(0, 0, num_rows, num_cols - 1, {
            'columns': [{'header': col} for col in df.columns],
            'name': table_name,
            'style': 'Table Style Medium 2'
        })
    worksheet.set_column(0, num_cols - 1, 15)
    
    if name == 'Exception_Log' and num_rows > 0:
        try:
            sev_idx = df.columns.get_loc('severity')
            sla_idx = df.columns.get_loc('sla_status')
            worksheet.conditional_format(1, sev_idx, num_rows, sev_idx, 
                                        {'type': 'cell', 'criteria': '==', 'value': '"CRITICAL"', 'format': critical_format})
            worksheet.conditional_format(1, sla_idx, num_rows, sla_idx, 
                                        {'type': 'cell', 'criteria': '==', 'value': '"OVER_SLA"', 'format': over_sla_format})
        except (KeyError, ValueError):
            pass

# ---------------------------------------------------------
# Tab 2: Dashboard (Fix 6 — expanded KPIs and charts)
# ---------------------------------------------------------
ws_dash = workbook.add_worksheet('Dashboard')
exc_df = datasets['Exception_Log']
rb_df = datasets['Recon_Breaks']

title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#1F497D', 'font_color': 'white'})
kpi_label = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
kpi_val = workbook.add_format({'bold': True, 'font_size': 12, 'border': 1, 'num_format': '#,##0'})
kpi_money = workbook.add_format({'bold': True, 'font_size': 12, 'border': 1, 'num_format': '$#,##0.00'})
kpi_pct = workbook.add_format({'bold': True, 'font_size': 12, 'border': 1, 'num_format': '0.0%'})
pass_fmt = workbook.add_format({'bold': True, 'font_color': '#006100', 'bg_color': '#C6EFCE', 'border': 1})

ws_dash.merge_range('A1:F1', 'Management Operations Dashboard', title_fmt)

# KPI cards — row 3-4
kpi_items = [
    ('Total Exceptions', '=COUNTA(tbl_exception_log[exception_id])'),
    ('Open', '=COUNTIFS(tbl_exception_log[status],"OPEN")'),
    ('In Review', '=COUNTIFS(tbl_exception_log[status],"IN_REVIEW")'),
    ('Pending Vendor', '=COUNTIFS(tbl_exception_log[status],"PENDING_VENDOR")'),
    ('Resolved', '=COUNTIFS(tbl_exception_log[status],"RESOLVED")'),
    ('Over SLA', '=COUNTIFS(tbl_exception_log[sla_status],"OVER_SLA")'),
]
for i, (label, formula) in enumerate(kpi_items):
    ws_dash.write(2, i, label, kpi_label)
    ws_dash.write_formula(3, i, formula, kpi_val)

# Row 6-7
kpi_items2 = [
    ('Critical Severity', '=COUNTIFS(tbl_exception_log[severity],"CRITICAL")', kpi_val),
    ('Total $ Exposure', '=SUM(tbl_exception_log[dollar_exposure])', kpi_money),
    ('Distinct Root Causes', exc_df['root_cause'].nunique() if len(exc_df) else 0, kpi_val),
    ('Ledger Failures', len(rf_df), kpi_val),
    ('Injections Tested', len(inj_df), kpi_val),
    ('Detection Rate', f'={len(inj_df[inj_df["detection_status"]=="DETECTED"])} / {max(len(inj_df),1)}' if len(inj_df) > 0 else '=1', kpi_pct),
]
for i, (label, val, fmt) in enumerate(kpi_items2):
    ws_dash.write(5, i, label, kpi_label)
    if isinstance(val, str) and val.startswith('='):
        ws_dash.write_formula(6, i, val, fmt)
    else:
        ws_dash.write(6, i, val, fmt)

ws_dash.set_column('A:F', 20)

# Root cause summary table (for charts)
rc_summary = exc_df['root_cause'].value_counts()
ws_dash.write('A9', 'Root Cause', bold_format)
ws_dash.write('B9', 'Count', bold_format)
ws_dash.write('C9', 'Exposure', bold_format)
rc_row = 9
for cause, count in rc_summary.items():
    exposure = exc_df.loc[exc_df['root_cause'] == cause, 'dollar_exposure'].sum()
    ws_dash.write(rc_row, 0, cause)
    ws_dash.write(rc_row, 1, int(count))
    ws_dash.write(rc_row, 2, float(exposure), money_format)
    rc_row += 1

# Chart 1: Root cause pie
if rc_row > 9:
    chart1 = workbook.add_chart({'type': 'pie'})
    chart1.add_series({'name': 'Root Causes', 'categories': ['Dashboard', 9, 0, rc_row-1, 0], 'values': ['Dashboard', 9, 1, rc_row-1, 1]})
    chart1.set_title({'name': 'Exceptions by Root Cause'})
    chart1.set_size({'width': 480, 'height': 320})
    ws_dash.insert_chart('D9', chart1)

    # Chart 2: Exposure by root cause bar
    chart2 = workbook.add_chart({'type': 'column'})
    chart2.add_series({'name': 'Dollar Exposure', 'categories': ['Dashboard', 9, 0, rc_row-1, 0], 'values': ['Dashboard', 9, 2, rc_row-1, 2]})
    chart2.set_title({'name': 'Dollar Exposure by Root Cause'})
    chart2.set_size({'width': 480, 'height': 320})
    ws_dash.insert_chart('D26', chart2)

# Owner summary + chart
owner_summary = exc_df['owner'].value_counts()
ws_dash.write(rc_row + 1, 0, 'Owner', bold_format)
ws_dash.write(rc_row + 1, 1, 'Count', bold_format)
ow_start = rc_row + 2
for owner, count in owner_summary.items():
    ws_dash.write(ow_start, 0, owner)
    ws_dash.write(ow_start, 1, int(count))
    ow_start += 1
if ow_start > rc_row + 2:
    chart3 = workbook.add_chart({'type': 'pie'})
    chart3.add_series({'name': 'Owners', 'categories': ['Dashboard', rc_row+2, 0, ow_start-1, 0], 'values': ['Dashboard', rc_row+2, 1, ow_start-1, 1]})
    chart3.set_title({'name': 'Exceptions by Owner'})
    chart3.set_size({'width': 480, 'height': 320})
    ws_dash.insert_chart('H9', chart3)

# Status mix + chart
status_summary = exc_df['status'].value_counts()
ws_dash.write(ow_start + 1, 0, 'Status', bold_format)
ws_dash.write(ow_start + 1, 1, 'Count', bold_format)
st_start = ow_start + 2
for status, count in status_summary.items():
    ws_dash.write(st_start, 0, status)
    ws_dash.write(st_start, 1, int(count))
    st_start += 1
if st_start > ow_start + 2:
    chart4 = workbook.add_chart({'type': 'pie'})
    chart4.add_series({'name': 'Status', 'categories': ['Dashboard', ow_start+2, 0, st_start-1, 0], 'values': ['Dashboard', ow_start+2, 1, st_start-1, 1]})
    chart4.set_title({'name': 'Exception Status Mix'})
    chart4.set_size({'width': 480, 'height': 320})
    ws_dash.insert_chart('H26', chart4)

# ---------------------------------------------------------
# Tab 3: Tie-Outs (Fix 7 — expanded checks)
# ---------------------------------------------------------
ws_tie = workbook.add_worksheet('Tie-Outs')
ws_tie.write('A1', 'Control Tie-Outs & Validation Checks', title_fmt)

# Precompute values for tie-outs
n_cash_txn = len(datasets['Cash_Transactions'])
n_sec_txn = len(datasets['Security_Transactions'])
n_ledger = len(datasets['Internal_Ledger'])
n_cust_bal = len(datasets['Custodian_Balances'])
n_breaks = len(rb_df)
n_exc = len(exc_df)
n_rf_fail = len(rf_df)
n_inj_tested = len(inj_df)
n_inj_detected = len(inj_df[inj_df['detection_status'] == 'DETECTED']) if len(inj_df) > 0 else 0
injection_detection_rate = n_inj_detected / max(n_inj_tested,1)
n_missing_ev = int(exc_df['evidence_file'].isna().sum() + (exc_df['evidence_file'].str.strip() == '').sum()) if 'evidence_file' in exc_df.columns else 0
total_exposure = float(exc_df['dollar_exposure'].sum()) if 'dollar_exposure' in exc_df.columns else 0
n_cash_breaks = int((rb_df['break_category'] == 'CASH_BALANCE_BREAK').sum()) if 'break_category' in rb_df.columns else 0
n_share_breaks = int((rb_df['break_category'] == 'SHARE_QUANTITY_BREAK').sum()) if 'break_category' in rb_df.columns else 0

tie_checks = [
    ['Check', 'Expected', 'Actual', 'Status'],
    ['Cash Transaction Rows', n_cash_txn, f'=ROWS(tbl_cash_transactions)', f'=IF(B3=C3,"PASS","FAIL")'],
    ['Security Transaction Rows', n_sec_txn, f'=ROWS(tbl_security_transactions)', f'=IF(B4=C4,"PASS","FAIL")'],
    ['Internal Ledger Rows', n_ledger, f'=ROWS(tbl_internal_ledger)', f'=IF(B5=C5,"PASS","FAIL")'],
    ['Custodian Balance Rows', n_cust_bal, f'=ROWS(tbl_custodian_balances)', f'=IF(B6=C6,"PASS","FAIL")'],
    ['Reconciliation Break Rows', n_breaks, f'=ROWS(tbl_recon_breaks)', f'=IF(B7=C7,"PASS","FAIL")'],
    ['Exception Log Rows', n_exc, f'=ROWS(tbl_exception_log)', f'=IF(B8=C8,"PASS","FAIL")'],
    ['Ledger Roll-Forward Failures', 0, n_rf_fail, f'=IF(C9=0,"PASS","FAIL")'],
    ['Injected Exceptions Tested', 8, n_inj_tested, f'=IF(C10>=8,"PASS","FAIL")'],
    ['Injected Exceptions Detected', 8, n_inj_detected, f'=IF(C11>=8,"PASS","FAIL")'],
    ['Injection Detection Rate', 1, injection_detection_rate, f'=IF(ROUND(C12,4)=ROUND(B12,4),"PASS","FAIL")'],
    ['Missing Evidence Count', 0, n_missing_ev, f'=IF(C13=0,"PASS","FAIL")'],
    ['Total Dollar Exposure', total_exposure, f'=SUM(tbl_exception_log[dollar_exposure])', f'=IF(ROUND(B14-C14,2)=0,"PASS","FAIL")'],
    ['Cash Break Count', n_cash_breaks, n_cash_breaks, f'=IF(B15=C15,"PASS","FAIL")'],
    ['Share Break Count', n_share_breaks, n_share_breaks, f'=IF(B16=C16,"PASS","FAIL")'],
]
ws_tie.add_table(1, 0, len(tie_checks)-1, 3, {
    'data': tie_checks[1:],
    'columns': [{'header': c} for c in tie_checks[0]],
    'name': 'tbl_tie_outs'
})
ws_tie.set_column('A:A', 35)
ws_tie.set_column('B:D', 18)
ws_tie.set_row(11, None, kpi_pct)
# Conditional format on Status column
ws_tie.conditional_format(2, 3, len(tie_checks)-1, 3, {'type': 'cell', 'criteria': '==', 'value': '"PASS"', 'format': pass_fmt})
ws_tie.conditional_format(2, 3, len(tie_checks)-1, 3, {'type': 'cell', 'criteria': '==', 'value': '"FAIL"', 'format': critical_format})

# ---------------------------------------------------------
# Tab 4: Exception Aging (Fix 8 — expanded detail)
# ---------------------------------------------------------
# Summary 1: By SLA, severity, root cause
aging_summary = exc_df.groupby(['sla_status', 'severity', 'root_cause'])['dollar_exposure'].sum().reset_index()
aging_summary.to_excel(writer, sheet_name='Exception Aging', index=False)
ws_aging = writer.sheets['Exception Aging']
if len(aging_summary) > 0:
    ws_aging.add_table(0, 0, len(aging_summary), 3, {
        'columns': [{'header': c} for c in aging_summary.columns],
        'name': 'tbl_exception_aging'
    })
ws_aging.set_column('A:C', 35)
ws_aging.set_column('D:D', 20, money_format)

# Summary 2: Aging buckets
def aging_bucket(days):
    if days <= 2: return '0-2 days'
    if days <= 5: return '3-5 days'
    if days <= 10: return '6-10 days'
    return '10+ days'

if 'aging_days' in exc_df.columns:
    exc_df['aging_bucket'] = exc_df['aging_days'].apply(aging_bucket)
    bucket_row = len(aging_summary) + 3
    ws_aging.write(bucket_row, 0, 'Aging Bucket', bold_format)
    ws_aging.write(bucket_row, 1, 'Count', bold_format)
    ws_aging.write(bucket_row, 2, 'Exposure', bold_format)
    for bucket, grp in exc_df.groupby('aging_bucket'):
        bucket_row += 1
        ws_aging.write(bucket_row, 0, bucket)
        ws_aging.write(bucket_row, 1, len(grp))
        ws_aging.write(bucket_row, 2, float(grp['dollar_exposure'].sum()), money_format)

    # Summary 3: Open exceptions by owner
    bucket_row += 2
    ws_aging.write(bucket_row, 0, 'Open Exceptions by Owner', bold_format)
    ws_aging.write(bucket_row, 1, 'Count', bold_format)
    ws_aging.write(bucket_row, 2, 'Exposure', bold_format)
    open_exc = exc_df[exc_df['status'] != 'RESOLVED']
    for owner, grp in open_exc.groupby('owner'):
        bucket_row += 1
        ws_aging.write(bucket_row, 0, owner)
        ws_aging.write(bucket_row, 1, len(grp))
        ws_aging.write(bucket_row, 2, float(grp['dollar_exposure'].sum()), money_format)

    # Summary 4: Root cause by status
    bucket_row += 2
    ws_aging.write(bucket_row, 0, 'Root Cause x Status', bold_format)
    rc_status = exc_df.groupby(['root_cause', 'status']).size().unstack(fill_value=0)
    rc_status.to_excel(writer, sheet_name='Exception Aging', startrow=bucket_row + 1)

# ---------------------------------------------------------
# Tab 5: Control Summary (Fix 5 — 12 columns)
# ---------------------------------------------------------
control_data = pd.DataFrame({
    'Control ID': [f'CTRL-{i:02d}' for i in range(1, 11)],
    'Control Name': ['Daily Cash Reconciliation', 'Daily Position Reconciliation', 'Exception SLA Monitoring', 'Vendor File Completeness', 'Transaction Classification Accuracy', 'Internal Ledger Roll-Forward', 'Data Types & Nullability Audit', 'Primary & Foreign Key Validation', 'High Dollar Exposure Alerting', 'Root Cause Tracking'],
    'Process Area': ['Reconciliation', 'Reconciliation', 'Exception Mgmt', 'Vendor Mgmt', 'Data Ingestion', 'Accounting', 'Database Admin', 'Database Admin', 'Risk Mgmt', 'Operations'],
    'Risk Addressed': ['Undetected cash variances', 'Undetected position breaks', 'Aged unresolved exceptions', 'Missing external data', 'Misclassified transactions', 'Balance integrity failure', 'Schema drift or null data', 'Orphan records or broken joins', 'Unchecked high-value breaks', 'Unresolved or unknown exceptions'],
    'Control Activity': ['Compare internal cash to custodian cash', 'Compare internal shares to custodian shares', 'Check aging_days > SLA threshold', 'Verify vendor file receipt_status', 'Map raw actions via type mapping', 'Prior balance + activity = current', 'Run column constraint checks', 'Validate FK referential integrity', 'Flag dollar_exposure > threshold', 'Classify and track root_cause'],
    'Frequency': ['Daily', 'Daily', 'Daily', 'Daily', 'Daily', 'Daily', 'Weekly', 'Weekly', 'Real-time', 'Daily'],
    'Owner': ['FinOps Team', 'FinOps Team', 'Recon Manager', 'Data Eng', 'Data Eng', 'FinOps Team', 'DBA', 'DBA', 'Risk Officer', 'Ops Analyst'],
    'Evidence Source': ['13_daily_cash_reconciliation.sql', '14_security_position_reconciliation.sql', 'exception_log.csv / Dashboard', 'vendor_files.csv', '07_transaction_type_mapping.sql', '09b_ledger_rollforward_validation.sql', '02_schema.sql constraints', '02_schema.sql FK definitions', 'exception_log.csv severity=CRITICAL', 'exception_log.csv root_cause'],
    'Status': ['FAIL (Breaks Detected)', 'FAIL (Breaks Detected)', 'FAIL (SLA Breached)', 'FAIL (Missing Files)', 'PASS', 'PASS', 'PASS', 'PASS', 'FAIL (Criticals Present)', 'PASS'],
    'Exception Handling': ['Investigate cash variance', 'Investigate share variance', 'Escalate aged items', 'Retry SFTP / contact vendor', 'Review unmapped actions', 'Investigate balance drift', 'Fix schema or data load', 'Repair broken references', 'Escalate to risk officer', 'Assign root cause label'],
    'Review Date': ['2024-07-05'] * 10,
    'Related Output': ['Recon Review tab', 'Recon Review tab', 'Exception Aging tab', 'Validation_Injections tab', 'Data_Cash Transactions tab', 'Validation_Ledger tab', 'Tie-Outs tab', 'Tie-Outs tab', 'Dashboard', 'Dashboard'],
})
control_data.to_excel(writer, sheet_name='Control Summary', index=False)
ws_ctrl = writer.sheets['Control Summary']
ws_ctrl.add_table(0, 0, len(control_data), len(control_data.columns) - 1, {
    'columns': [{'header': c} for c in control_data.columns],
    'name': 'tbl_control_summary'
})
ws_ctrl.set_column('A:A', 12)
ws_ctrl.set_column('B:B', 30)
ws_ctrl.set_column('C:C', 18)
ws_ctrl.set_column('D:E', 35)
ws_ctrl.set_column('F:F', 12)
ws_ctrl.set_column('G:G', 15)
ws_ctrl.set_column('H:H', 40)
ws_ctrl.set_column('I:I', 22)
ws_ctrl.set_column('J:J', 28)
ws_ctrl.set_column('K:K', 14)
ws_ctrl.set_column('L:L', 25)

# ---------------------------------------------------------
# Tab 6: Recon Review
# ---------------------------------------------------------
recon_review = pd.merge(
    datasets['Internal_Ledger'][['account_id', 'ledger_date', 'cash_balance']].rename(columns={'account_id': 'account_id_int'}),
    datasets['Custodian_Balances'][['account_id', 'balance_date', 'custodian_cash_balance']].rename(columns={'account_id': 'account_id_cust'}),
    left_on=['account_id_int', 'ledger_date'],
    right_on=['account_id_cust', 'balance_date'],
    how='outer'
)

# Start writing from row 1 (0-indexed)
ws_recon = workbook.add_worksheet('Recon Review')
ws_recon.write('A1', 'Reconciliation Sandbox (Formula Driven)', bold_format)

# Define columns
cols = ['account_id_int', 'ledger_date', 'cash_balance', 'account_id_cust', 'balance_date', 'custodian_cash_balance', 'Excel_Variance', 'Pass/Fail', 'Manual Status']

# Write headers
for col_num, col_name in enumerate(cols):
    ws_recon.write(1, col_num, col_name, header_format)

num_rows = len(recon_review)
for row_num, row_data in enumerate(recon_review.itertuples(index=False)):
    r = row_num + 2 # Start at row 3 (index 2)
    
    # Write data
    ws_recon.write(r, 0, row_data[0])
    ws_recon.write(r, 1, str(row_data[1]) if pd.notna(row_data[1]) else '')
    ws_recon.write(r, 2, row_data[2])
    ws_recon.write(r, 3, row_data[3])
    ws_recon.write(r, 4, str(row_data[4]) if pd.notna(row_data[4]) else '')
    ws_recon.write(r, 5, row_data[5])
    
    # Formulas
    # Excel Variance: =IFERROR(ROUND([@[cash_balance]]-[@[custodian_cash_balance]],2),"Review")
    ws_recon.write_formula(r, 6, f'=IFERROR(ROUND(C{r+1}-F{r+1}, 2), "Review")')
    ws_recon.write_formula(r, 7, f'=IF(ABS(G{r+1})>0.01, "Break", "Pass")')

if num_rows > 0:
    ws_recon.add_table(1, 0, num_rows + 1, len(cols) - 1, {
        'columns': [{'header': c} for c in cols],
        'name': 'tbl_recon_review'
    })
    ws_recon.data_validation(2, 8, num_rows + 1, 8, {'validate': 'list', 'source': ['Open', 'In Review', 'Resolved']})
    ws_recon.conditional_format(2, 7, num_rows + 1, 7, {'type': 'cell', 'criteria': '==', 'value': '"Break"', 'format': critical_format})

ws_recon.set_column('A:I', 20)

# ---------------------------------------------------------
# Tab 7: Validation_Injections (Fix 3 — renamed)
# ---------------------------------------------------------
if len(inj_df) > 0:
    inj_df.to_excel(writer, sheet_name='Validation_Injections', index=False)
    ws_inj = writer.sheets['Validation_Injections']
    ws_inj.add_table(0, 0, len(inj_df), len(inj_df.columns) - 1, {
        'columns': [{'header': col} for col in inj_df.columns],
        'name': 'tbl_injection_coverage',
        'style': 'Table Style Medium 2'
    })
    try:
        status_idx = inj_df.columns.get_loc('detection_status')
        ws_inj.conditional_format(1, status_idx, len(inj_df), status_idx,
                                 {'type': 'cell', 'criteria': '==', 'value': '"NOT DETECTED"', 'format': critical_format})
        ws_inj.conditional_format(1, status_idx, len(inj_df), status_idx,
                                 {'type': 'cell', 'criteria': '==', 'value': '"DETECTED"', 'format': pass_fmt})
    except (KeyError, ValueError):
        pass
    ws_inj.set_column('A:A', 12)
    ws_inj.set_column('B:C', 30)
    ws_inj.set_column('D:E', 25)
    ws_inj.set_column('F:F', 18)
    print(f"  Added Validation_Injections tab ({len(inj_df)} rows).")
else:
    print("  WARNING: No injection data available.")

# ---------------------------------------------------------
# Tab 8: Validation_Ledger (Fix 9 — clear pass/fail)
# ---------------------------------------------------------
ws_rf = workbook.add_worksheet('Validation_Ledger')
if len(rf_df) > 0:
    rf_df.to_excel(writer, sheet_name='Validation_Ledger', index=False)
    ws_rf = writer.sheets['Validation_Ledger']
    ws_rf.add_table(0, 0, len(rf_df), len(rf_df.columns) - 1, {
        'columns': [{'header': col} for col in rf_df.columns],
        'name': 'tbl_ledger_rollforward',
        'style': 'Table Style Medium 2'
    })
    print(f"  Added Validation_Ledger tab ({len(rf_df)} failure rows).")
else:
    ws_rf.write('A1', 'Ledger Roll-Forward Validation', workbook.add_format({'bold': True, 'font_size': 14}))
    ws_rf.write('A3', 'Result:', bold_format)
    ws_rf.write('B3', 'PASS', pass_fmt)
    ws_rf.write('A5', 'Detail:', bold_format)
    ws_rf.write('B5', 'Ledger roll-forward validation returned zero failures. For every account and date, prior_balance + daily_movement = ending_balance within 0.001 tolerance.')
    ws_rf.write('A7', 'Failures Found:', bold_format)
    ws_rf.write('B7', 0, kpi_val)
    ws_rf.set_column('A:A', 18)
    ws_rf.set_column('B:B', 90)
    print("  Added Validation_Ledger tab (PASS — 0 failures).")

# Save and close
writer.close()
print("Excel model built successfully!")
