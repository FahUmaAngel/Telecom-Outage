import sqlite3
import os

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print(f"Inspecting records in {db_path}...")
    cursor.execute("SELECT id, incident_id, start_time, end_time FROM outages WHERE id BETWEEN 20 AND 30;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
