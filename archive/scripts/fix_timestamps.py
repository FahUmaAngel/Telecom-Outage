import sqlite3
import re

def fix_timestamp_string(ts):
    if not ts or not isinstance(ts, str):
        return ts
    
    # Check for extra quotes
    if '"' in ts:
        # Strategy: strip quotes from ends first, then handle middle ones
        cleaned = ts.strip('"')
        
        # If there's still a quote in the middle, it's likely a separator for offset
        # e.g. 2025-12-27 18:49:18"01:00
        if '"' in cleaned:
            # Replace middle quote with + if it looks like an offset
            cleaned = re.sub(r'"(\d{2}:\d{2})', r'+\1', cleaned)
            # Remove any remaining stray quotes
            cleaned = cleaned.replace('"', '')
            
        return cleaned

    return ts

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("SELECT id, start_time, end_time, estimated_fix_time FROM outages WHERE operator_id IN (1, 2)")
    rows = cur.fetchall()
    
    print(f"Checking {len(rows)} records for broken timestamps...")
    fixed_count = 0
    
    for row in rows:
        oid, st, et, eft = row
        new_st = fix_timestamp_string(st)
        new_et = fix_timestamp_string(et)
        new_eft = fix_timestamp_string(eft)
        
        if new_st != st or new_et != et or new_eft != eft:
            cur.execute(
                "UPDATE outages SET start_time = ?, end_time = ?, estimated_fix_time = ? WHERE id = ?",
                (new_st, new_et, new_eft, oid)
            )
            fixed_count += 1
            
    conn.commit()
    conn.close()
    print(f"Finished. Fixed timestamps for {fixed_count} records.")

if __name__ == "__main__":
    main()
