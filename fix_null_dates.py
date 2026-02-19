import sqlite3
import os

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print(f"Cleaning up null start_times in {db_path}...")
    
    # Update start_time to created_at if start_time is null
    cursor.execute("""
        UPDATE outages 
        SET start_time = created_at 
        WHERE start_time IS NULL;
    """)
    
    affected = cursor.rowcount
    conn.commit()
    print(f"Successfully updated {affected} records.")
    
except Exception as e:
    print(f"Error during cleanup: {e}")
    conn.rollback()
finally:
    conn.close()
