import sqlite3
import json

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT o.incident_id, o.title, op.name
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
    """)
    rows = cur.fetchall()
    
    mismatches = {'telia': 0, 'tre': 0, 'lycamobile': 0, 'telenor': 0, 'tele2': 0, 'halebop': 0}
    
    for r in rows:
        inc_id, title_raw, op_name = r
        if not inc_id: continue
        
        try:
            title_dict = json.loads(title_raw) if title_raw else {}
            title_sv = title_dict.get('sv', '')
            title_en = title_dict.get('en', '')
            
            if title_sv != inc_id or title_en != inc_id:
                mismatches[op_name.lower()] = mismatches.get(op_name.lower(), 0) + 1
        except Exception as e:
            mismatches[op_name.lower()] = mismatches.get(op_name.lower(), 0) + 1
            
    print("Mismatched Titles by Operator:")
    for op, val in mismatches.items():
        if val > 0:
            print(f"  {op}: {val}")
            
    # Sample mismatched Telia titles
    cur.execute("""
        SELECT o.incident_id, o.title
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'telia'
        LIMIT 10
    """)
    print("\nSample Telia titles:")
    for r in cur.fetchall():
        print(f"  ID: {r[0]}")
        print(f"  Title: {r[1]}")
            
if __name__ == "__main__":
    main()
