
import sqlite3
import time

try:
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    start = time.time()
    cursor.execute("SELECT operator, MAX(scraped_at) FROM raw_data GROUP BY operator")
    rows = cursor.fetchall()
    end = time.time()
    print(f"Query took {end - start:.4f} seconds")
    print(f"Results: {rows}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
