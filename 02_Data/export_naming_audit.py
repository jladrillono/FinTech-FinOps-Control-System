"""
export_naming_audit.py

Purpose:
    Queries the SQL Server FinOps_Control_System database to identify any
    objects or columns that violate the project's lowercase_snake_case
    naming convention. Exports results to naming_audit.csv.

Usage:
    python export_naming_audit.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine
import warnings

warnings.filterwarnings('ignore')

engine = create_engine(
    'mssql+pyodbc://localhost/FinOps_Control_System'
    '?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes'
)

query = """
SELECT 'OBJECT' AS issue_type, s.name AS schema_name, o.name AS object_name, NULL AS column_name, o.type_desc 
FROM sys.objects o 
JOIN sys.schemas s ON o.schema_id = s.schema_id 
WHERE o.is_ms_shipped = 0 AND o.type IN ('U', 'V') AND ( o.name COLLATE Latin1_General_BIN LIKE '%[A-Z]%' OR o.name LIKE '% %' OR o.name LIKE '%-%' ) 
UNION ALL 
SELECT 'COLUMN' AS issue_type, s.name AS schema_name, t.name AS object_name, c.name AS column_name, 'COLUMN' AS type_desc 
FROM sys.tables t 
JOIN sys.schemas s ON t.schema_id = s.schema_id 
JOIN sys.columns c ON t.object_id = c.object_id 
WHERE c.name COLLATE Latin1_General_BIN LIKE '%[A-Z]%' OR c.name LIKE '% %' OR c.name LIKE '%-%' 
ORDER BY issue_type, schema_name, object_name, column_name;
"""

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'naming_audit.csv')
df = pd.read_sql(query, engine)
df.to_csv(output_path, index=False)
print(f"Exported {len(df)} rows to {output_path}")
