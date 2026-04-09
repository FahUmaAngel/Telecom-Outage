import sqlite3

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Select all Telia incidents where location ends with ', Unknown'
    cur.execute("""
        SELECT o.id, o.incident_id, o.location
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'telia'
        AND o.location LIKE '%, Unknown'
    """)
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} incidents to clean.")
    
    updated = 0
    for row in rows:
        oid, inc_id, old_loc = row
        # Remove ', Unknown' from the end
        new_loc = old_loc.replace(', Unknown', '')
        
        print(f"[{inc_id}] {old_loc} -> {new_loc}")
        cur.execute("UPDATE outages SET location = ? WHERE id = ?", (new_loc, oid))
        updated += 1
        
    conn.commit()
    conn.close()
    print(f"Finished. Updated {updated} incidents.")

if __name__ == "__main__":
    main()
