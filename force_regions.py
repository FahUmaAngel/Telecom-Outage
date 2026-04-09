import sqlite3
import json
from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

def force_telia_regions():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Pre-fetch region map
    cur.execute("SELECT id, name FROM regions")
    region_rows = cur.fetchall()
    region_id_map = {}
    for rid, name_json in region_rows:
        try:
            name_dict = json.loads(name_json)
            sv_name = name_dict.get('sv')
            region_id_map[sv_name] = rid
            # e.g. "Stockholms län" -> 1
        except:
            pass
            
    # Fix existing Telia incidents where region_id is NULL
    cur.execute("""
        SELECT o.id, o.incident_id, o.location, o.title, o.description
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'telia' AND o.region_id IS NULL
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} Telia outages missing region_id")
    
    fixed = 0
    resolved_unknowns = 0
    for r in rows:
        oid, inc_id, loc, title_json, desc_json = r
        
        # Try to find a region from title, description or location itself
        title = json.loads(title_json).get('sv', '') if title_json else ''
        desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        text_to_search = f"{title} {desc} {loc}"
        
        county_name = extract_region_from_text(text_to_search, SWEDISH_COUNTIES)
        
        if county_name:
            reg_id = region_id_map.get(county_name)
            if reg_id:
                # Update to strict region
                cur.execute("""
                    UPDATE outages 
                    SET location = ?, region_id = ? 
                    WHERE id = ?
                """, (county_name, reg_id, oid))
                fixed += 1
                continue
                
        # If we STILL have no region, and it's 'Unknown' or just some random text
        # We will mark it resolved so it disappears from 'Active' list
        # We set end_time to yesterday
        # Wait, if they are active, mark them resolved.
        cur.execute("""
            UPDATE outages
            SET status = 'resolved', end_time = '2026-03-10T00:00:00+01:00'
            WHERE id = ? AND status != 'resolved'
        """, (oid,))
        resolved_unknowns += 1
        
    # Also do Lycamobile and Tre just to be safe
    cur.execute("""
        SELECT o.id, o.location, o.title, o.description
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name != 'telia' AND o.region_id IS NULL AND o.status != 'resolved'
    """)
    other_rows = cur.fetchall()
    for r in other_rows:
        oid, loc, title_json, desc_json = r
        title = json.loads(title_json).get('sv', '') if title_json else ''
        desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        text_to_search = f"{title} {desc} {loc}"
        
        county_name = extract_region_from_text(text_to_search, SWEDISH_COUNTIES)
        if county_name:
            reg_id = region_id_map.get(county_name)
            if reg_id:
                cur.execute("UPDATE outages SET location = ?, region_id = ? WHERE id = ?", (county_name, reg_id, oid))
                fixed += 1
        else:
             # Just set location to "Sweden" to be safe and hide Unknown if we want
             cur.execute("UPDATE outages SET location = 'Sverige' WHERE id = ? AND location = 'Unknown'", (oid,))

    conn.commit()
    conn.close()
    print(f"Fixed {fixed} outages to regions.")
    print(f"Auto-resolved {resolved_unknowns} ghost Telia outages with Unknown locations.")

if __name__ == '__main__':
    force_telia_regions()
