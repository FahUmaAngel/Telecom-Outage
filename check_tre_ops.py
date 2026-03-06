import sqlite3
import pandas as pd

conn = sqlite3.connect('telecom_outage.db')

print("Operators:")
df_ops = pd.read_sql_query("SELECT id, name FROM operators", conn)
print(df_ops.to_string())

print("\nTre Outages grouped by Operator ID:")
df_outages = pd.read_sql_query("""
    SELECT operator_id, count(*) as count 
    FROM outages 
    WHERE title LIKE '%Tre%' OR operator_id = 3
    GROUP BY operator_id
""", conn)
print(df_outages.to_string())

conn.close()
