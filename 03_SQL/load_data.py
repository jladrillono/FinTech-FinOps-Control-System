import os
import pandas as pd
from sqlalchemy import create_engine
import urllib

# Paths — resolve dynamically from script location
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base_path, "02_Data", "raw_stock_transactions.csv")

# Create connection string for SQLAlchemy
# Using TrustServerCertificate=yes since we are using local dev instance
params = urllib.parse.quote_plus(
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=localhost;'
    'Database=FinOps_Control_System;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

print("Loading CSV...")
df = pd.read_csv(csv_path)

# Make sure columns exactly match the SQL table except for IDENTITY column
# The SQL table has source_row_id as IDENTITY
print("Inserting data into raw.raw_stock_transactions...")
try:
    df.to_sql(
        name='raw_stock_transactions',
        schema='raw',
        con=engine,
        if_exists='append',
        index=False
    )
    print("Data load complete!")
except Exception as e:
    print(f"Error during data load: {e}")
