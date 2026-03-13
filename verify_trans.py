import sqlite3
import json
import os

db_path = 'telecom_outage.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit()

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT description FROM outages WHERE description IS NOT NULL LIMIT 10")
rows = cur.fetchall()

print(f"Checking {len(rows)} records...")
for i, row in enumerate(rows):
    try:
        data = json.loads(row[0])
        sv = data.get('sv', '')
        en = data.get('en', '')
        print(f"Record {i+1}:")
        print(f"  SV: {sv[:50]}...")
        print(f"  EN: {en[:50]}...")
        if sv.lower() == en.lower() and sv:
            print("  [!] Match (Potentially untranslated)")
        else:
            print("  [+] Different (Translated)")
    except Exception as e:
        print(f"  Error parsing record {i+1}: {e}")

conn.close()
