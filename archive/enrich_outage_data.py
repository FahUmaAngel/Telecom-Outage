from openlocationcode import openlocationcode as olc
import sqlite3
from geopy.geocoders import Nominatim
import time
import sys

def enrich_data():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch records that have coordinates but need enrichment
    # - Missing place (Plus Code)
    # - OR Location is a placeholder (same as incident_id or generic)
    query = """
        SELECT o.id, o.incident_id, o.latitude, o.longitude, o.location, o.place, op.name as operator_name
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL
        AND (o.place IS NULL OR o.place = '' 
             OR o.location IS NULL OR o.location = 'Unknown' OR o.location = 'Sverige'
             OR o.location = o.incident_id)
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} records needing enrichment.")
    
    geolocator = Nominatim(user_agent="TelecomOutageEnricher/1.0")
    
    updated_count = 0
    for row in rows:
        oid = row['id']
        inc_id = row['incident_id']
        lat, lon = row['latitude'], row['longitude']
        current_loc = row['location']
        current_place = row['place']
        
        new_place = current_place
        new_loc = current_loc
        
        # A. Generate Plus Code if missing
        if not current_place or len(current_place) < 5:
            new_place = olc.encode(lat, lon)
        
        # B. Reverse Geocode if location is placeholder
        is_placeholder = (not current_loc or current_loc == 'Unknown' or 
                         current_loc == 'Sverige' or current_loc == inc_id or 
                         current_loc.startswith('{')) # Handle JSON string artifacts
        
        if is_placeholder:
            try:
                print(f"[{inc_id}] Reverse geocoding ({lat}, {lon})...")
                time.sleep(1.2) # Rate limit
                location = geolocator.reverse(f"{lat}, {lon}", language='en')
                if location:
                    addr = location.raw.get('address', {})
                    city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality') or addr.get('suburb')
                    county = addr.get('state') or addr.get('county')
                    
                    if city and county:
                        new_loc = f"{city}, {county}"
                    elif city:
                        new_loc = city
                    elif county:
                        new_loc = county
                    else:
                        new_loc = location.address.split(',')[0] # Fallback to first part of address
            except Exception as e:
                print(f"  Error geocoding {inc_id}: {e}")

        # C. Update Database if anything changed
        if new_place != current_place or new_loc != current_loc:
            cursor.execute("""
                UPDATE outages 
                SET place = ?, location = ? 
                WHERE id = ?
            """, (new_place, new_loc, oid))
            updated_count += 1
            print(f"  Updated {inc_id}: Place={new_place}, Loc={new_loc}")
            
            # Commit every 10 updates
            if updated_count % 10 == 0:
                conn.commit()
                print(f"--- Committed {updated_count} updates ---")

    conn.commit()
    conn.close()
    print(f"Finished. Total records enriched: {updated_count}")

if __name__ == "__main__":
    enrich_data()
