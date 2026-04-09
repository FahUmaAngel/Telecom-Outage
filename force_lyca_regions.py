import sqlite3
import json
from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

def force_lyca_regions():
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
        except:
            pass
            
    # Find active Lycamobile outages
    cur.execute("""
        SELECT o.id, o.location, o.region_id, o.title, o.description
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'lycamobile'
    """)
    rows = cur.fetchall()
    print(f"Total Lycamobile outages: {len(rows)}")
    
    fixed_county_word = 0
    assigned_region = 0
    
    for r in rows:
        oid, loc, reg_id, title_json, desc_json = r
        loc = loc or ""
        
        # 1. Clean the word "County" or "county" if present
        if "county" in loc.lower():
            # e.g., "Stockholms län (Stockholm County)" or just "Stockholm County"
            # It's better to just re-extract the exact Swedish Region name
            pass # Handling below
            
        # Try to find a region from title, description or location itself
        title = json.loads(title_json).get('sv', '') if title_json else ''
        desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        text_to_search = f"{title} {desc} {loc}"
        
        county_name = extract_region_from_text(text_to_search, SWEDISH_COUNTIES)
        
        if county_name:
            # We found a valid Swedish region name (e.g., 'Stockholms län')
            reg_id = region_id_map.get(county_name)
            if reg_id:
                # Update DB to strictly use the Swedish region name and link region_id
                cur.execute("""
                    UPDATE outages 
                    SET location = ?, region_id = ? 
                    WHERE id = ?
                """, (county_name, reg_id, oid))
                
                if "county" in loc.lower():
                    fixed_county_word += 1
                if r[2] is None:
                    assigned_region += 1
        else:
            # If no region could be found, set location to 'Sverige' (Sweden)
             # to hide ugly raw strings or "Unknown"
             cur.execute("UPDATE outages SET location = 'Sverige' WHERE id = ? AND location != 'Sverige'", (oid,))

    conn.commit()
    conn.close()
    print(f"Removed English 'County' suffix from {fixed_county_word} Lycamobile locations.")
    print(f"Assigned strict Region ID to {assigned_region} Lycamobile locations.")

if __name__ == '__main__':
    force_lyca_regions()
