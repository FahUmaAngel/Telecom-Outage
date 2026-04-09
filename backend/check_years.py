import sqlite3
import os

db_path = "telecom_outage.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check table existence and column names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")

    if ('outages',) in tables:
        # Check years in start_time or created_at
        cursor.execute("PRAGMA table_info(outages);")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns in outages: {columns}")

        date_col = None
        if 'start_time' in columns:
            date_col = 'start_time'
        elif 'created_at' in columns:
            date_col = 'created_at'
        
        if date_col:
            # Extract year from the date string. SQLite handles YYYY-MM-DD format.
            query = f"SELECT DISTINCT strftime('%Y', {date_col}) FROM outages;"
            cursor.execute(query)
            years = cursor.fetchall()
            print(f"Years found in {date_col}: {[y[0] for y in years if y[0]]}")
        else:
            print("No date column found in outages table.")
    else:
        print("Outages table not found.")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
