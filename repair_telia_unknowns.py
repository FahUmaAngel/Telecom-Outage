import sqlite3
import json
import sys
import os

# Add scrapers to path to use engine/translation
sys.path.append(os.getcwd())
from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES
from scrapers.common.geocoding import get_county_coordinates

def repair_telia_unknowns():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Find all Telia "Unknown" records
    cursor.execute("""
        SELECT i.id, i.incident_id, i.location, i.description, o.name 
        FROM outages i 
        JOIN operators o ON i.operator_id = o.id 
        WHERE o.name = 'telia' AND (i.location LIKE '%Unknown%' OR i.location = 'Sweden' OR i.location = 'Sverige')
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} Telia records with poor location data.")
    
    fixed_count = 0
    for row in rows:
        db_id, inc_id, loc, desc_json, op_name = row
        
        # Try to find a better location from description
        desc_text = ""
        try:
            desc_data = json.loads(desc_json)
            desc_text = f"{desc_data.get('sv', '')} {desc_data.get('en', '')}"
        except:
            desc_text = str(desc_json)
            
        # Also check raw_data if available? 
        # For now, desc_text usually contains the location clues like "Malmö", "Stockholm"
        
        county_name = extract_region_from_text(desc_text, SWEDISH_COUNTIES)
        if not county_name:
            # Maybe the incident ID itself or context has clues? 
            # Telia incidents usually have "området: X" in description
            pass
            
        if county_name:
            print(f"Fixed {inc_id}: {loc} -> {county_name}")
            coords = get_county_coordinates(county_name, jitter=True)
            if coords:
                cursor.execute("""
                    UPDATE outages 
                    SET location = ?, latitude = ?, longitude = ? 
                    WHERE id = ?
                """, (county_name, coords[0], coords[1], db_id))
            else:
                cursor.execute("""
                    UPDATE outages SET location = ? WHERE id = ?
                """, (county_name, db_id))
            fixed_count += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully repaired {fixed_count} Telia records.")

if __name__ == "__main__":
    repair_telia_unknowns()
