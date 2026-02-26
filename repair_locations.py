
import sqlite3
import json
import logging
import sys
import os

# Add parent dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RepairLocations")

def repair():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    logger.info(f"Connected to {db_path}")
    
    # 1. Find all outages with non-standard locations
    # Get official counties lists
    from scrapers.common.translation import SWEDISH_COUNTIES
    
    placeholders = ','.join(['?'] * len(SWEDISH_COUNTIES))
    query = f'SELECT id, title, description, location FROM outages WHERE location NOT IN ({placeholders})'
    
    cursor.execute(query, SWEDISH_COUNTIES)
    rows = cursor.fetchall()
    
    if not rows:
        logger.info("No outages with unstandardized locations found.")
    else:
        logger.info(f"Found {len(rows)} outages with unstandardized location. Attempting repair...")
        
        repaired_count = 0
        from scrapers.common.geocoding import SWEDISH_COUNTY_COORDS
        
        for row in rows:
            outage_id, title_json, desc_json, old_location = row
            
            # First try the location text itself since it might just be slightly misspelled (e.g. Västernorrland län)
            new_location = extract_region_from_text(old_location, SWEDISH_COUNTIES)
            if not new_location:
                # Fallback to title/desc if location string didn't yield anything
                try:
                    title_sv = json.loads(title_json).get('sv', '') if title_json else ''
                    desc_sv = json.loads(desc_json).get('sv', '') if desc_json else ''
                except:
                    title_sv = ''
                    desc_sv = ''
                    
                context_text = f"{title_sv} {desc_sv}"
                new_location = extract_region_from_text(context_text, SWEDISH_COUNTIES)
            
            if new_location and new_location != "Unknown":
                cursor.execute(
                    'UPDATE outages SET location = ? WHERE id = ?',
                    (new_location, outage_id)
                )
                repaired_count += 1
                
        conn.commit()
        logger.info(f"✓ Successfully standardized {repaired_count} locations.")
        
    # 2. Update coordinates based on the new locations
    from scrapers.common.geocoding import SWEDISH_COUNTY_COORDS
    
    cursor.execute('SELECT id, location FROM outages WHERE latitude IS NULL OR latitude = 0')
    rows_no_coords = cursor.fetchall()
    
    coord_count = 0
    for row in rows_no_coords:
        outage_id, location = row
        if location in SWEDISH_COUNTY_COORDS:
            coords = SWEDISH_COUNTY_COORDS[location]
            cursor.execute(
                'UPDATE outages SET latitude = ?, longitude = ? WHERE id = ?',
                (coords[0], coords[1], outage_id)
            )
            coord_count += 1
            
    conn.commit()
    logger.info(f"✓ Updated coordinates for {coord_count} records.")
    
    conn.close()

if __name__ == "__main__":
    repair()
