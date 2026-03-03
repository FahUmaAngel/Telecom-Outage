import sqlite3
import json
import os
import sys

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

def fix_orebro_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Fetch all Telia outages that are currently Stockholms län 
    # and might actually belong to Örebro län based on text or raw data.
    # To be safe, we will just look for ANY Telia outage that mentions Örebro 
    # but is assigned to Stockholms län (or something else).
    
    cursor.execute("""
        SELECT i.id, i.incident_id, i.location, i.description, o.name 
        FROM outages i 
        JOIN operators o ON i.operator_id = o.id 
        WHERE o.name = 'telia'
    """)
    rows = cursor.fetchall()
    
    to_fix = []
    for row in rows:
        db_id, inc_id, loc, desc_json, op_name = row
        text_to_search = f"{desc_json}".lower()
        if 'örebro' in text_to_search and loc != 'Örebro län':
            to_fix.append((db_id, inc_id, loc))
            
    # If we couldn't find it in description, maybe the user wants to point out specific ones?
    # Let me just check the raw data JSON as well if possible.
    if not to_fix:
        cursor.execute("""
            SELECT i.id, i.incident_id, i.location, r.content
            FROM outages i
            JOIN operators o ON i.operator_id = o.id
            LEFT JOIN raw_outages r ON i.raw_data_id = r.id
            WHERE o.name = 'telia'
        """)
        raw_rows = cursor.fetchall()
        for r in raw_rows:
            db_id, inc_id, loc, raw_content = r
            if raw_content and 'örebro' in raw_content.lower() and loc != 'Örebro län':
                if not any(x[0] == db_id for x in to_fix):
                     to_fix.append((db_id, inc_id, loc))

    print(f"Found {len(to_fix)} Telia incidents mentioning Örebro but mapped to other regions.")
    
    count = 0
    correct_location = "Örebro län"
    coords = get_county_coordinates(correct_location, jitter=True)
    lat = coords[0] if coords else 59.2741
    lon = coords[1] if coords else 15.2066
    
    for db_id, inc_id, old_loc in to_fix:
        print(f"Fixing {inc_id} (Was: {old_loc}) -> {correct_location}")
        cursor.execute("""
            UPDATE outages
            SET location = ?, latitude = ?, longitude = ?
            WHERE id = ?
        """, (correct_location, lat, lon, db_id))
        count += 1
        
    # As a fallback, if the user noticed specific ones but they don't explicitly say "Örebro" in our DB text because our scraper messed up:
    # Let's print all recent Stockholms län Telia incidents just to inspect.
    if count == 0:
        print("\nNo explicit matches found. Here are the latest Telia 'Stockholms län' incidents:")
        cursor.execute("""
            SELECT incident_id, start_time 
            FROM outages 
            WHERE operator_id = (SELECT id FROM operators WHERE name = 'telia') AND location = 'Stockholms län'
            ORDER BY id DESC LIMIT 10
        """)
        for r in cursor.fetchall():
            print(f"{r[0]} | {r[1]}")
            
    conn.commit()
    conn.close()
    print(f"\nCorrection complete. {count} records updated.")

if __name__ == "__main__":
    fix_orebro_locations()
