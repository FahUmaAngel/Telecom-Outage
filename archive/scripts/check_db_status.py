
import sqlite3
import os

db_path = r"d:\94 FAH works\Telecom-Outage\telecom_outage.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Latest Status ---")
    cursor.execute("SELECT MAX(start_time), MAX(created_at) FROM outages;")
    row = cursor.fetchone()
    print(f"Max Start Time: {row[0]}")
    print(f"Max Created At: {row[1]}")
    
    cursor.execute("SELECT MAX(scraped_at) FROM raw_data;")
    row = cursor.fetchone()
    print(f"Max Scraped At: {row[0]}")
    
    print("\n--- Outages per Day (Last 7 Days) ---")
    cursor.execute("""
        SELECT date(start_time), COUNT(*) 
        FROM outages 
        WHERE start_time IS NOT NULL 
        GROUP BY date(start_time) 
        ORDER BY date(start_time) DESC 
        LIMIT 10;
    """)
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} outages")


    print("\n--- Outages per Day (April 2026) ---")
    cursor.execute("""
        SELECT date(start_time), COUNT(*) 
        FROM outages 
        WHERE start_time >= '2026-04-01' AND start_time < '2026-05-01'
        GROUP BY date(start_time) 
        ORDER BY date(start_time) ASC;
    """)
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} outages")
        
    conn.close()
