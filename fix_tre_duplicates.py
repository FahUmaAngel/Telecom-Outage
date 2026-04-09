"""
Script to:
1. Remove duplicate Tre outages from DB (keep latest, with correct data)
2. Fix end_time which is NULL for active Tre incidents
"""
import sqlite3
import json
from datetime import datetime

def fix_tre_data():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    print("Step 1: Finding duplicate Tre outages...")
    cur.execute("""
        SELECT incident_id, COUNT(*) as cnt, MAX(id) as keep_id, MIN(id) as remove_start
        FROM outages
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre')
        GROUP BY incident_id
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    print(f"Found {len(duplicates)} incident IDs with duplicates.")
    
    for inc_id, cnt, keep_id, _ in duplicates:
        # Delete all EXCEPT the newest (keep_id = MAX(id))
        cur.execute("""
            DELETE FROM outages
            WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre')
              AND incident_id = ?
              AND id != ?
        """, (inc_id, keep_id))
    
    print(f"  Removed duplicate rows.")
    
    # Step 2: Fix NULL end_times for active Tre incidents by re-parsing from raw data
    print("\nStep 2: Fixing NULL end_times from raw data...")
    cur.execute("""
        SELECT o.id, o.raw_data_id, rd.data
        FROM outages o
        JOIN raw_data rd ON o.raw_data_id = rd.id
        WHERE o.operator_id = (SELECT id FROM operators WHERE name = 'tre')
          AND o.end_time IS NULL
          AND o.status != 'resolved'
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} active Tre incidents with NULL end_time.")
    
    fixed_end = 0
    for oid, raw_id, raw_json in rows:
        try:
            raw = json.loads(raw_json)
            # Check the raw Tre dump for end_time
            # The source format stores in 'source'  if this was from the scraper
            end = raw.get('end_time') or raw.get('Arbete klart') or raw.get('end')
            if end:
                # Parse a datetime from it - it may be ISO or human-readable
                try:
                    if 'T' in end:
                        dt = datetime.fromisoformat(end)
                    else:
                        import re
                        # format: "2026-03-18 Kl 03:00" or "2026-03-18T03:00:00"
                        clean = re.sub(r'[Kk][Ll]\s*', '', end).strip()
                        dt = datetime.strptime(clean, "%Y-%m-%d %H:%M")
                    cur.execute("UPDATE outages SET end_time = ? WHERE id = ?", (dt.isoformat(), oid))
                    fixed_end += 1
                except:
                    pass
        except Exception as e:
            pass
    
    print(f"  Fixed end_time for {fixed_end} incidents.")
    
    conn.commit()
    conn.close()
    
    print("\nAll done!")

if __name__ == "__main__":
    fix_tre_data()
