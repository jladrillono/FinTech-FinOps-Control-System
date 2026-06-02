import os
import pandas as pd
from sqlalchemy import create_engine

# Define paths — resolve dynamically from script location
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "02_Data")
os.makedirs(data_dir, exist_ok=True)

# Database connection using SQLAlchemy
engine = create_engine('mssql+pyodbc://localhost/FinOps_Control_System?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes')

try:
    print("Connecting to SQL Server for Phase 5 exports...")
    
    exports = {
        'reconciliation_breaks.csv': 'SELECT * FROM core.reconciliation_breaks',
        'exception_log.csv': 'SELECT * FROM core.exception_log',
        'ledger_rollforward_validation.csv': '''
            WITH DailyActivity AS (
                SELECT account_id, transaction_date AS activity_date, SUM(cash_impact) AS daily_cash_movement
                FROM core.cash_transactions GROUP BY account_id, transaction_date
            ),
            RollForward AS (
                SELECT curr.account_id, curr.ledger_date, curr.cash_balance AS ending_balance,
                    ISNULL(prev.cash_balance, 0) AS prior_balance, ISNULL(act.daily_cash_movement, 0) AS daily_movement,
                    ISNULL(prev.cash_balance, 0) + ISNULL(act.daily_cash_movement, 0) AS calculated_ending_balance
                FROM core.internal_ledger_balances curr
                LEFT JOIN core.internal_ledger_balances prev ON curr.account_id = prev.account_id AND prev.ledger_date = DATEADD(day, -1, curr.ledger_date)
                LEFT JOIN DailyActivity act ON curr.account_id = act.account_id AND curr.ledger_date = act.activity_date
            )
            SELECT 'Roll-Forward Failure' AS CheckName, account_id, ledger_date, prior_balance, daily_movement, calculated_ending_balance, ending_balance, (calculated_ending_balance - ending_balance) AS variance
            FROM RollForward WHERE ABS(calculated_ending_balance - ending_balance) > 0.001
        ''',
        'injection_to_break_validation.csv': '''
            SELECT eil.injection_id, eil.exception_type, eil.expected_detection_rule,
             COALESCE(rb_counts.detected_break_count, 0) + COALESCE(el_counts.detected_exception_count, 0) AS detected_break_count,
             COALESCE(rb_counts.cumulative_detected_exposure, 0) + COALESCE(el_counts.cumulative_exception_exposure, 0) AS cumulative_detected_exposure,
             CASE WHEN COALESCE(rb_counts.detected_break_count, 0) + COALESCE(el_counts.detected_exception_count, 0) > 0 THEN 'DETECTED' ELSE 'NOT DETECTED' END AS detection_status
            FROM ctl.exception_injection_log eil
            LEFT JOIN (
                SELECT injection_id, COUNT(break_id) AS detected_break_count, SUM(dollar_exposure) AS cumulative_detected_exposure
                FROM core.reconciliation_breaks
                GROUP BY injection_id
            ) rb_counts ON rb_counts.injection_id = eil.injection_id
            LEFT JOIN (
                SELECT eil2.injection_id, COUNT(el.exception_id) AS detected_exception_count, SUM(el.dollar_exposure) AS cumulative_exception_exposure
                FROM core.exception_log el
                JOIN ctl.exception_injection_log eil2 ON el.root_cause = eil2.exception_type COLLATE SQL_Latin1_General_CP1_CI_AS
                    OR (el.root_cause = 'MISSING_VENDOR_FILE' AND eil2.exception_type = 'Missing Vendor File')
                    OR (el.root_cause = 'WRONG_ACCOUNT_POSTING' AND eil2.exception_type = 'Wrong Account Posting')
                WHERE el.break_id IS NULL
                GROUP BY eil2.injection_id
            ) el_counts ON el_counts.injection_id = eil.injection_id
            ORDER BY eil.injection_id;
        '''
    }

    for filename, query in exports.items():
        filepath = os.path.join(data_dir, filename)
        print(f"Exporting {filename}...")
        df = pd.read_sql(query, engine)
        df.to_csv(filepath, index=False)
        print(f"Exported {len(df)} rows to {filename}.")

    print("Phase 5 exports completed successfully.")

except Exception as e:
    print(f"An error occurred: {e}")
