import sqlite3
import json
import hashlib
from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

def sanitize_tre():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # 1. Fetch regions
    cur.execute("SELECT id, name FROM regions")
    region_rows = cur.fetchall()
    region_id_map = {}
    for rid, name_json in region_rows:
        try:
            name_dict = json.loads(name_json)
            sv_name = name_dict.get('sv')
            region_id_map[sv_name] = rid
        except: pass
            
    # 2. Find all Tre active outages
    cur.execute("""
        SELECT o.id, o.incident_id, o.location, o.title, o.region_id
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'tre'
    """)
    rows = cur.fetchall()
    
    fixed_ids = 0
    fixed_regions = 0
    
    for r in rows:
        oid, inc_id, loc, title_json, reg_id = r
        
        needs_update = False
        updates = {}
        
        # A) Fix Incident ID and Title
        if inc_id and 'tre_' in inc_id:
            # Hash the ugly string into a nice 6-char hex string
            hash_str = hashlib.md5(inc_id.encode()).hexdigest()[:6].upper()
            new_id = f"TRE-{hash_str}"
            
            updates['incident_id'] = new_id
            
            # Since user wants title to match incident_id
            new_title = json.dumps({"sv": new_id, "en": new_id})
            updates['title'] = new_title
            
            needs_update = True
            fixed_ids += 1
            
        # B) Fix Location -> Region
        if not reg_id or (loc and "län" not in loc.lower() and loc != 'Sverige'):
            title = json.loads(title_json).get('sv', '') if title_json else ''
            # Use raw unhashed ID if it conveys location (like the old 'tre_Värmland' string did)
            text_to_search = f"{title} {loc} {inc_id}"
            county_name = extract_region_from_text(text_to_search, SWEDISH_COUNTIES)
            if county_name:
                updates['location'] = county_name
                reg = region_id_map.get(county_name)
                if reg:
                    updates['region_id'] = reg
                needs_update = True
                fixed_regions += 1
            else:
                 updates['location'] = 'Sverige'
                 needs_update = True
                 
        if needs_update:
            # Build query dynamically based on dict
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [oid]
            cur.execute(f"UPDATE outages SET {set_clause} WHERE id = ?", values)

    conn.commit()
    conn.close()
    print(f"Sanitized #{fixed_ids} ugly Tre incident IDs into short hashes.")
    print(f"Enforced strict Region mapping on #{fixed_regions} Tre locations.")

if __name__ == '__main__':
    sanitize_tre()
