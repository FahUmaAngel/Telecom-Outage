import sqlite3
import pandas as pd

conn = sqlite3.connect('telecom_outage.db')
conn.execute('PRAGMA busy_timeout = 10000')

df = pd.read_sql_query("""
    SELECT status, COUNT(*) as count 
    FROM outages 
    WHERE operator_id = (SELECT id FROM operators WHERE name = 'Tre') 
    GROUP BY status
""", conn)
print("Tre Outages grouped by Status in DB:")
print(df.to_string())

df_all = pd.read_sql_query("""
    SELECT incident_id, start_time, end_time, status
    FROM outages 
    WHERE operator_id = (SELECT id FROM operators WHERE name = 'Tre') 
    LIMIT 10
""", conn)
print("\nSample Tre Outages:")
print(df_all.to_string())

conn.close()
