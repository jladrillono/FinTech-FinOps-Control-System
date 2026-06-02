Write-Host "Rebuilding FinOps Database..."

$server = "localhost"
$db = "FinOps_Control_System"
$scripts = @(
    "01_create_database.sql",
    "02_schema.sql"
)

# 1. Run DB creation and schema
foreach ($script in $scripts) {
    Write-Host "Running $script..."
    sqlcmd -S $server -E -C -i $script
}

# 2. Load data via python
Write-Host "Running python data load..."
python load_data.py

# 3. Run remaining SQL scripts
$scripts2 = @(
    "03_staging_tables.sql",
    "04_core_tables.sql",
    "05_transformations.sql",
    "06_reporting_views.sql",
    "07_validation_checks.sql",
    "08_ledger_balances.sql",
    "09_security_positions.sql",
    "09b_ledger_rollforward_validation.sql",
    "10_custodian_simulation.sql",
    "11_exception_injection.sql",
    "12_phase4_validation_checks.sql",
    "13_daily_cash_reconciliation.sql",
    "14_security_position_reconciliation.sql",
    "15_transaction_match_reconciliation.sql",
    "16_exception_detection.sql",
    "17_phase5_validation_checks.sql"
)

foreach ($script in $scripts2) {
    Write-Host "Running $script..."
    sqlcmd -S $server -E -C -i $script
}

# 4. Export Data
Write-Host "Exporting Phase 4 CSV files..."
python export_phase4_data.py

Write-Host "Exporting Phase 5 CSV files..."
python export_phase5_data.py

Write-Host "Pipeline Rebuild Complete!"
