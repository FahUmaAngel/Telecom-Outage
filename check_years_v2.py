import sqlite3
import os

# The uvicorn command runs from the root, so the DB should be in the root
db_path = "telecom_outage.db"
if not os.path.exists(db_path):
    # Try backend path just in case
    db_path = "backend/telecom_outage.db"

print(f"Checking database at: {os.path.abspath(db_path)}")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")

    if 'outages' in tables:
        cursor.execute("PRAGMA table_info(outages);")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns in outages: {columns}")

        date_col = None
        if 'start_time' in columns:
            date_col = 'start_time'
        elif 'created_at' in columns:
            date_col = 'created_at'
        
        if date_col:
            query = f"SELECT DISTINCT strftime('%Y', {date_col}) FROM outages;"
            cursor.execute(query)
            years = [y[0] for y in cursor.fetchall() if y[0]]
            print(f"Years found in {date_col}: {years}")
            
            if not years:
                # Maybe strftime didn't work, let's try raw values
                cursor.execute(f"SELECT DISTINCT {date_col} FROM outages LIMIT 5;")
                samples = cursor.fetchall()
                print(f"Sample raw values in {date_col}: {samples}")
        else:
            print("No date column found in outages table.")
    else:
        print("Outages table not found.")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
