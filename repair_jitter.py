import sqlite3
import random
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.geocoding import get_county_coordinates, SWEDISH_COUNTY_COORDS

def repair_jitter():
    print("Starting coordinate jitter repair...")
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # We want to target incidents that have EXACTLY the central coordinates of any county
    target_count = 0
    updated_count = 0
    
    for county, center in SWEDISH_COUNTY_COORDS.items():
        lat, lng = center
        # Find all outages with these exact coordinates
        cursor.execute("""
            SELECT id FROM outages 
            WHERE latitude = ? AND longitude = ?
        """, (lat, lng))
        
        outage_ids = [r[0] for r in cursor.fetchall()]
        if not outage_ids:
            continue
            
        print(f"Found {len(outage_ids)} incidents at center of {county}")
        target_count += len(outage_ids)
        
        for oid in outage_ids:
            # Apply jitter
            new_lat, new_lng = get_county_coordinates(county, jitter=True)
            cursor.execute("""
                UPDATE outages SET latitude = ?, longitude = ? 
                WHERE id = ?
            """, (new_lat, new_lng, oid))
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f"Repair complete. Updated {updated_count} incidents out of {target_count} targets.")

if __name__ == "__main__":
    repair_jitter()
