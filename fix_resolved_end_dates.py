import sqlite3
from datetime import datetime

def fix_end_dates():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Update end_time to now for all explicitly resolved Tre incidents that lack a region
    # and have an end_time in the future.
    now = datetime.utcnow().isoformat()
    
    # We will just fix all Tre outages that are "resolved" but have end_time > now.
    cur.execute("""
        UPDATE outages
        SET end_time = ?
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre')
          AND status = 'resolved'
          AND (end_time > ? OR end_time IS NULL)
    """, (now, now))
    
    print(f"Fixed {cur.rowcount} Tre incidents that were resolved but had future/null end dates.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_end_dates()
