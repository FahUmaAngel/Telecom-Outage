import sqlite3
import json

def analyze_descriptions():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.id, op.name as operator, o.incident_id, o.location, o.title, o.description
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE o.location IN ('Sverige', 'Unknown', 'sweden', 'unknown')
        ORDER BY o.start_time DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for r in rows:
        out_id, op, inc_id, loc, title_json, desc_json = r
        try:
            title = json.loads(title_json).get('sv', '') if title_json else ''
            desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        except:
            title = str(title_json)
            desc = str(desc_json)
        print(f"[{op}] ID:{inc_id} Loc:{loc}")
        print(f"  Title: {title}")
        print(f"  Desc: {desc}")
        print("-" * 40)
    
    conn.close()

if __name__ == '__main__':
    analyze_descriptions()
