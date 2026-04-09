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
    ids_fixed = 0
    
    for r in rows:
        oid, inc_id, title_raw, op_name = r
        
        # 1. Fix missing IDs for Tre
        if not inc_id and op_name.lower() == 'tre':
            # Try to reconstruct ID from location and start_time (stored as ISO in DB)
            cur.execute("SELECT location, start_time FROM outages WHERE id = ?", (oid,))
            loc, start = cur.fetchone()
            if loc and start:
                reconstructed_id = f"tre_{loc}_{start.replace(' ', '_')}"
                cur.execute("UPDATE outages SET incident_id = ? WHERE id = ?", (reconstructed_id, oid))
                inc_id = reconstructed_id
                ids_fixed += 1
        
        if not inc_id: continue
        
        # 2. Standardize Titles
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
    print(f"Finished. Standardized {updated} incident titles and fixed {ids_fixed} missing IDs.")

if __name__ == "__main__":
    main()
