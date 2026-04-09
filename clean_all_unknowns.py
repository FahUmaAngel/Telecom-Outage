import sqlite3

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()

cur.execute("""
    SELECT o.id, o.incident_id, o.location
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'telia'
    AND o.location LIKE '%Unknown%'
""")
rows = cur.fetchall()

print(f"Found {len(rows)} incidents with 'Unknown' in location.")

updated = 0
for row in rows:
    oid, inc_id, old_loc = row
    
    # Strip out any 'Unknown' variations
    parts = [p.strip() for p in old_loc.split(',')]
    clean_parts = [p for p in parts if p.lower() != 'unknown' and p != '']
    
    if clean_parts:
        new_loc = ", ".join(clean_parts)
    else:
        new_loc = "Unknown"  # Failsafe if the entire string was "Unknown, Unknown"
        
    print(f"[{inc_id}] {old_loc} -> {new_loc}")
    
    if old_loc != new_loc:
        cur.execute("UPDATE outages SET location = ? WHERE id = ?", (new_loc, oid))
        updated += 1

conn.commit()
conn.close()
print(f"Finished. Updated {updated} incidents.")
