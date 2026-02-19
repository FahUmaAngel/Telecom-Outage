import sqlite3
import os

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def audit_dates(table):
    print(f"\nAudit for {table}:")
    cursor.execute(f"PRAGMA table_info({table});")
    cols = [c[1] for c in cursor.fetchall() if 'time' in c[1].lower() or 'at' in c[1].lower()]
    
    for col in cols:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL OR {col} = 0 OR {col} = '' OR {col} = '0';")
        zeros = cursor.fetchone()[0]
        print(f"  {col}: {zeros} potentially problematic records (NULL, 0, or empty)")
        
        if zeros > 0:
            cursor.execute(f"SELECT id, {col} FROM {table} WHERE {col} IS NULL OR {col} = 0 OR {col} = '' OR {col} = '0' LIMIT 3;")
            print(f"    Samples: {cursor.fetchall()}")

audit_dates("outages")
audit_dates("user_reports")
conn.close()
