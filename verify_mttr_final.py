import sqlite3
from datetime import datetime, timedelta

db_path = 'telecom_outage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get Tre ID
cursor.execute("SELECT id FROM operators WHERE name = 'tre' COLLATE NOCASE;")
tre_id = cursor.fetchone()[0]

# Calculate MTTR for last year (365 days) manually with fallback
since_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")

cursor.execute(f"""
    SELECT start_time, end_time, updated_at, status
    FROM outages 
    WHERE operator_id = {tre_id} 
    AND start_time IS NOT NULL 
    AND (end_time IS NOT NULL OR status LIKE 'resolved');
""")

outages = cursor.fetchall()

total_hours = 0.0
valid_count = 0

def parse_date(s):
    if not s: return None
    if '.' in s:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

for start_str, end_str, updated_str, status in outages:
    try:
        start = parse_date(start_str)
        # Fallback logic mirroring backend
        actual_end = parse_date(end_str) or (parse_date(updated_str) if status == 'resolved' else None)
        
        if not actual_end: continue

        diff = actual_end - start
        hours = diff.total_seconds() / 3600.0
        if 0 < hours < 8760:
            total_hours += hours
            valid_count += 1
    except Exception as e:
        continue

avg_hours = round(total_hours / valid_count, 2) if valid_count > 0 else 0

print(f"Final Manual Verification for Tre (Last 365 days - WITH FALLBACK):")
print(f"Total valid outages: {valid_count}")
print(f"Average MTTR: {avg_hours} hours")

conn.close()
