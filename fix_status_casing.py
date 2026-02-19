import sqlite3
import os

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print(f"Fixing status casing in {db_path}...")
    
    # Map lowercase values to uppercase names
    cursor.execute("UPDATE outages SET status = 'ACTIVE' WHERE status = 'active';")
    cursor.execute("UPDATE outages SET status = 'RESOLVED' WHERE status = 'resolved';")
    cursor.execute("UPDATE outages SET status = 'INVESTIGATING' WHERE status = 'investigating';")
    cursor.execute("UPDATE outages SET status = 'SCHEDULED' WHERE status = 'scheduled';")
    
    affected = cursor.rowcount
    conn.commit()
    print(f"Cleanup complete. Note: cursor.rowcount only shows the last statement's impact.")
    
    # Check current distribution
    cursor.execute("SELECT status, count(*) FROM outages GROUP BY status;")
    print("New distribution:")
    for row in cursor.fetchall():
        print(row)
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
