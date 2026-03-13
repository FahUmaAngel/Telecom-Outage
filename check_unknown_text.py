import sqlite3
import json

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT incident_id, title, description
        FROM outages
        WHERE location = 'Unknown'
        AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
    """)
    rows = cur.fetchall()
    
    print(f"Checking text logs for {len(rows)} Unknown incidents...")
    for r in rows[:10]:
        inc_id, title_raw, desc_raw = r
        try:
            title = json.loads(title_raw).get('sv', '') if title_raw else ''
            desc = json.loads(desc_raw).get('sv', '') if desc_raw else ''
        except:
            title = title_raw
            desc = desc_raw
        
        print(f"[{inc_id}]")
        print(f"  Title: {title}")
        print(f"  Desc:  {desc[:100]}...\n")

if __name__ == "__main__":
    main()
