import sqlite3
import json

def list_bad_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.id, op.name as operator, o.incident_id, o.location, o.title, o.description
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE o.location IN ('Sverige', 'Unknown', 'sweden', 'unknown')
        ORDER BY o.start_time DESC
    """)
    rows = cursor.fetchall()
    print(f"Total incidents with bad locations: {len(rows)}")
    for r in rows:
        out_id, op, inc_id, loc, title_json, desc_json = r
        try:
            title = json.loads(title_json).get('sv', '') if title_json else ''
            desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        except:
            title = str(title_json)
            desc = str(desc_json)
        print(f"[{op}] ID:{inc_id} (DB ID:{out_id}) Loc:{loc}")
        print(f"  Title: {title[:100]}")
        # print(f"  Desc: {desc[:100]}")
    
    conn.close()

if __name__ == '__main__':
    list_bad_locations()
