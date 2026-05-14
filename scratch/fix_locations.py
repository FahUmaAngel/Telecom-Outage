import sqlite3
import requests
import time
import json

def get_db_path():
    return 'telecom_outage.db'

def reverse_geocode(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
        headers = {'User-Agent': 'TelecomOutageFixer/1.0'}
        
        time.sleep(1.1)  # Respect rate limit
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get('address', {})
            
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality')
            if city:
                if ' kommun' in city:
                    city = city.replace(' kommun', '')
                return city
            county = addr.get('county')
            if county:
                return county
    except Exception as e:
        print(f"Error geocoding {lat}, {lon}: {e}")
    return None

def main():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get all outages with unknown location
    cursor.execute("""
        SELECT id, latitude, longitude 
        FROM outages 
        WHERE (location = 'Unknown' OR location IS NULL OR location = '') 
        AND latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} outages with unknown location to fix.")
    
    cache = {}
    updates = 0
    
    for row in rows:
        outage_id, lat, lon = row
        coord_key = f"{lat},{lon}"
        
        if coord_key not in cache:
            loc = reverse_geocode(lat, lon)
            cache[coord_key] = loc
            print(f"Resolved {coord_key} to {loc}")
        
        loc = cache[coord_key]
        if loc:
            cursor.execute("UPDATE outages SET location = ? WHERE id = ?", (loc, outage_id))
            updates += 1
            
    conn.commit()
    conn.close()
    print(f"Updated {updates} outages with new locations.")

if __name__ == '__main__':
    main()
