import sqlite3
import requests
import time
import re
import json

def get_coordinates(query):
    """Simple forward geocoding using Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query + ", Sweden",
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'TelecomOutageMonitor/1.0 (Recovery Script)'}
    
    try:
        time.sleep(1.2) # Respect rate limits
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.json():
            data = resp.json()[0]
            return float(data['lat']), float(data['lon']), data['display_name']
    except Exception as e:
        print(f"  Geocoding error for '{query}': {e}")
    return None, None, None

def main():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    log_path = 'd:/94 FAH works/Telecom-Outage/telia_descriptions.txt'
    
    # 1. Parse log file
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Map IDs (Lines 8-32 in 1-based is 7-31 in 0-based)
    # Descriptions (Lines 39-63 in 1-based is 38-62 in 0-based)
    id_lines = lines[7:32]
    desc_lines = lines[38:63]
    
    mapping = {}
    for i in range(len(id_lines)):
        id_match = re.search(r'INCSE\d+', id_lines[i])
        if id_match:
            inc_id = id_match.group(0)
            # Extract place name from description
            desc = desc_lines[i].split('|')[1].strip()
            
            # Use regex to find location words
            # Locations often follow 'i', 'nära', 'för', 'området'
            place = desc
            for keyword in [" i ", " nära ", " för ", " omkring "]:
                if keyword in desc:
                    place = desc.split(keyword)[1].split(".")[0].split(",")[0]
                    break
            
            # Clean up common suffixes
            place = re.sub(r'(trakten|området|område|regionen| läns område|läns| läns| län| och omgivningar)', '', place, flags=re.IGNORECASE).strip()
            
            # Edge case handling
            if "påverkar mobilnätet" in place.lower() or len(place) < 2:
                place = "Stockholm" # Global fallback for generic Telia issues
                
            mapping[inc_id] = place

    print(f"Extracted {len(mapping)} incident-to-location mappings.")
    
    # 2. Update Database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updated_count = 0
    for inc_id, search_query in mapping.items():
        # Check if already has coordinates to skip unnecessary API calls
        cursor.execute("SELECT latitude FROM outages WHERE incident_id = ? AND latitude IS NOT NULL", (inc_id,))
        if cursor.fetchone():
            continue
            
        print(f"Processing {inc_id} -> '{search_query}'...")
        lat, lon, full_name = get_coordinates(search_query)
        
        if lat and lon:
            # Clean up location name for DB
            clean_loc = full_name.split(',')[0]
            if len(full_name.split(',')) > 1:
                clean_loc += ", " + full_name.split(',')[-2].strip()
            
            cursor.execute("""
                UPDATE outages 
                SET latitude = ?, longitude = ?, location = ?
                WHERE incident_id = ? AND (latitude IS NULL OR longitude IS NULL)
                AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
            """, (lat, lon, clean_loc, inc_id))
            
            if cursor.rowcount > 0:
                print(f"  Success: {clean_loc} ({lat}, {lon})")
                updated_count += 1
            else:
                print(f"  Warning: No record found in DB for {inc_id} (missing coords)")
        else:
            print(f"  Failed: Could not geocode '{search_query}'")
            
    conn.commit()
    conn.close()
    
    print("-" * 40)
    print(f"Finished. Successfully updated {updated_count} incidents.")

if __name__ == "__main__":
    main()
