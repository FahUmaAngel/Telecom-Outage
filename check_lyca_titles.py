import sqlite3
import json

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT o.incident_id, o.title
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'lycamobile'
    """)
    rows = cur.fetchall()
    
    print("Sample Lycamobile mismatches:")
    for r in rows:
        inc_id, title_raw = r
        if not inc_id: continue
        
        try:
            title_dict = json.loads(title_raw) if title_raw else {}
            title_sv = title_dict.get('sv', '')
            title_en = title_dict.get('en', '')
            
            if title_sv != inc_id or title_en != inc_id:
                print(f"  ID: {inc_id}")
                print(f"  Title: {title_raw}")
        except Exception as e:
            pass
            
if __name__ == "__main__":
    main()
