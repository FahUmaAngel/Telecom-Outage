import sqlite3
import os

db_path = "telecom_outage.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def check_table(table_name):
    print(f"\n--- Checking table: {table_name} ---")
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        
        date_cols = [c for c in columns if 'time' in c or 'date' in c or 'at' in c]
        print(f"Date columns: {date_cols}")
        
        for col in date_cols:
            # Check for 0, NULL, or empty strings
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL OR {col} = 0 OR {col} = '';")
            count_invalid = cursor.fetchone()[0]
            print(f"  Column '{col}': {count_invalid} records with NULL/0/empty")
            
            # Check for dates starting with 1970
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} LIKE '1970%';")
            count_1970 = cursor.fetchone()[0]
            print(f"  Column '{col}': {count_1970} records starting with '1970'")
            
            if count_invalid > 0 or count_1970 > 0:
                cursor.execute(f"SELECT id, {col} FROM {table_name} WHERE {col} IS NULL OR {col} = 0 OR {col} = '' OR {col} LIKE '1970%' LIMIT 5;")
                samples = cursor.fetchall()
                print(f"  Sample records: {samples}")
                
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

check_table("outages")
check_table("user_reports")

conn.close()
