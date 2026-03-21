import sqlite3
import os
from datetime import datetime, timedelta

db_path = 'telecom_outage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get Tre ID
cursor.execute("SELECT id FROM operators WHERE name = 'tre' COLLATE NOCASE;")
tre_id = cursor.fetchone()[0]

# Calculate MTTR for last year (365 days) manually
since_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")

cursor.execute(f"""
    SELECT start_time, end_time 
    FROM outages 
    WHERE operator_id = {tre_id} 
    AND start_time >= '{since_date}'
    AND start_time IS NOT NULL 
    AND end_time IS NOT NULL;
""")

outages = cursor.fetchall()

total_hours = 0.0
valid_count = 0

for start_str, end_str in outages:
    try:
        # DB format can be 'YYYY-MM-DD HH:MM:SS.mmmmmm' or 'YYYY-MM-DD HH:MM:SS'
        def parse_date(s):
            if '.' in s:
                return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

        start = parse_date(start_str)
        end = parse_date(end_str)
        diff = end - start
        hours = diff.total_seconds() / 3600.0
        if 0 < hours < 8760:
            total_hours += hours
            valid_count += 1
    except Exception as e:
        continue

avg_hours = round(total_hours / valid_count, 2) if valid_count > 0 else 0

print(f"Manual Verification for Tre (Last 365 days):")
print(f"Total valid outages: {valid_count}")
print(f"Average MTTR: {avg_hours} hours")

conn.close()
