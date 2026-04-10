import sqlite3
import time
from geopy.geocoders import Nominatim
from openlocationcode import openlocationcode as olc

def recover_lyca_coords():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Identify Lycamobile incidents missing coordinates
    query = """
        SELECT o.id, o.incident_id, o.location 
        FROM outages o 
        JOIN operators op ON o.operator_id = op.id 
        WHERE op.name = 'lycamobile' AND (o.latitude IS NULL OR o.longitude IS NULL)
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} Lycamobile incidents missing coordinates.")
    
    geolocator = Nominatim(user_agent="LycaRecover/1.0")
    
    updated_count = 0
    for row in rows:
        oid = row['id']
        inc_id = row['incident_id']
        location_name = row['location']
        
        if not location_name or location_name == 'Unknown':
            print(f"Skipping {inc_id}: No valid location name.")
            continue
            
        print(f"Geocoding {inc_id} ({location_name})...")
        try:
            # Append Sweden for context
            search_query = f"{location_name}, Sweden"
            time.sleep(1.2) # Nominatim rate limit
            geo_result = geolocator.geocode(search_query)
            
            if geo_result:
                lat, lon = geo_result.latitude, geo_result.longitude
                plus_code = olc.encode(lat, lon)
                
                cursor.execute("""
                    UPDATE outages 
                    SET latitude = ?, longitude = ?, place = ?
                    WHERE id = ?
                """, (lat, lon, plus_code, oid))
                
                updated_count += 1
                print(f"  Success: {lat}, {lon} | PlusCode: {plus_code}")
                
                if updated_count % 10 == 0:
                    conn.commit()
            else:
                print(f"  Failed: Could not find coordinates for '{search_query}'")
                
        except Exception as e:
            print(f"  Error processing {inc_id}: {e}")

    conn.commit()
    conn.close()
    print(f"Finished. Total Lycamobile incidents updated: {updated_count}")

if __name__ == "__main__":
    recover_lyca_coords()
