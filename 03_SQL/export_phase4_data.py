import os
import pandas as pd
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine

# Define paths — resolve dynamically from script location
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "02_Data")

# Ensure directory exists
os.makedirs(data_dir, exist_ok=True)

# Database connection parameters
SERVER = 'localhost'
DATABASE = 'FinOps_Control_System'

try:
    print("Connecting to SQL Server...")
    engine = create_engine(f"mssql+pyodbc://{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes")
    print("Connected successfully.")

    # Tables to export
    exports = {
        'custodian_balances.csv': 'SELECT * FROM core.custodian_balances',
        'custodian_positions.csv': 'SELECT * FROM core.custodian_positions',
        'vendor_files.csv': 'SELECT * FROM ctl.vendor_files',
        'exception_injection_log.csv': 'SELECT * FROM ctl.exception_injection_log'
    }

    for filename, query in exports.items():
        filepath = os.path.join(data_dir, filename)
        print(f"Exporting {filename}...")
        df = pd.read_sql(query, engine)
        df.to_csv(filepath, index=False)
        print(f"Exported {len(df)} rows to {filename}.")

    print("All exports completed successfully.")

except Exception as e:
    print(f"An error occurred: {e}")
