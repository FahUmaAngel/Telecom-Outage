import sqlite3
import json

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT o.id, o.incident_id, o.title, op.name
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
    """)
    rows = cur.fetchall()
    
    updated = 0
    for r in rows:
        oid, inc_id, title_raw, op_name = r
        if not inc_id: continue
        
        needs_update = False
        try:
            title_dict = json.loads(title_raw) if title_raw else {}
            if title_dict.get('sv') != inc_id or title_dict.get('en') != inc_id:
                needs_update = True
        except:
            needs_update = True
            
        if needs_update:
            new_title = json.dumps({"sv": inc_id, "en": inc_id})
            cur.execute("UPDATE outages SET title = ? WHERE id = ?", (new_title, oid))
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"Finished. Standardized {updated} incident titles to their Incident IDs.")

if __name__ == "__main__":
    main()
