import sqlite3
import os

db_path = 'telecom_outage.db'
if not os.path.exists(db_path):
    print("Database not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Outages Status Count ---")
    cursor.execute("SELECT status, COUNT(*) FROM outages GROUP BY status")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- Recent Resolved Outages ---")
    cursor.execute("SELECT incident_id, operator_id, end_time FROM outages WHERE status = 'resolved' ORDER BY end_time DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Operator: {row[1]}, End Time: {row[2]}")

    print("\n--- Cleaning up legacy End Times for active outages ---")
    cursor.execute("UPDATE outages SET end_time = NULL WHERE status != 'resolved'")
    print(f"Cleared end_time for {cursor.rowcount} active outages.")
    conn.commit()

    conn.close()
