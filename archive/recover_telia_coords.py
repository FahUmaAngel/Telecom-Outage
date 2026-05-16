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

def _parse_telia_mapping(log_path):
    """Parse Telia log file to extract incident ID to location mappings."""
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    id_lines = lines[7:32]
    desc_lines = lines[38:63]
    
    mapping = {}
    for i in range(len(id_lines)):
        id_match = re.search(r'INCSE\d+', id_lines[i])
        if not id_match:
            continue
        inc_id = id_match.group(0)
        desc = desc_lines[i].split('|')[1].strip()
        
        place = desc
        for keyword in [" i ", " nära ", " för ", " omkring "]:
            if keyword in desc:
                place = desc.split(keyword)[1].split(".")[0].split(",")[0]
                break
        
        place = re.sub(
            r'(trakten|området|område|regionen| läns område|läns| läns| län| och omgivningar)',
            '',
            place,
            flags=re.IGNORECASE
        ).strip()
        
        if "påverkar mobilnätet" in place.lower() or len(place) < 2:
            place = "Stockholm"
        
        mapping[inc_id] = place
    return mapping


def _process_telia_incident(cursor, inc_id, search_query):
    """Process single Telia incident: check existing coords, geocode, update DB. Returns True if updated."""
    cursor.execute(
        "SELECT latitude FROM outages WHERE incident_id = ? AND latitude IS NOT NULL",
        (inc_id,)
    )
    if cursor.fetchone():
        return False
    
    print(f"Processing {inc_id} -> '{search_query}'...")
    lat, lon, full_name = get_coordinates(search_query)
    
    if not (lat and lon):
        print(f"  Failed: Could not geocode '{search_query}'")
        return False
    
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
        return True
    else:
        print(f"  Warning: No record found in DB for {inc_id} (missing coords)")
        return False


def main():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    log_path = 'd:/94 FAH works/Telecom-Outage/telia_descriptions.txt'
    
    mapping = _parse_telia_mapping(log_path)
    print(f"Extracted {len(mapping)} incident-to-location mappings.")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updated_count = 0
    for inc_id, search_query in mapping.items():
        if _process_telia_incident(cursor, inc_id, search_query):
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    print("-" * 40)
    print(f"Finished. Successfully updated {updated_count} incidents.")

if __name__ == "__main__":
    main()
