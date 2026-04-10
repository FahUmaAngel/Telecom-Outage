import sys
import os
import json
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def investigate():
    conn = sqlite3.connect('telecom_outage.db')
    c = conn.cursor()
    
    # Try to find records in raw_data that mention 2g or 3g
    c.execute("SELECT id, operator, data FROM raw_data WHERE LOWER(data) LIKE '%2g%' OR LOWER(data) LIKE '%3g%' OR LOWER(data) LIKE '%gsm%' OR LOWER(data) LIKE '%umts%'")
    rows = c.fetchall()
    
    print(f"Found {len(rows)} raw data rows mentioning 2G/3G/GSM/UMTS")
    
    for rowid, operator, data_str in rows[:5]:
        print(f"\n--- {operator} (ID: {rowid}) ---")
        try:
            data = json.loads(data_str)
            if isinstance(data, list) and data:
                print(json.dumps(data[0], indent=2)[:500] + "...")
            else:
                print(json.dumps(data, indent=2)[:500] + "...")
        except:
            print(data_str[:500])
            
    conn.close()

if __name__ == '__main__':
    investigate()
