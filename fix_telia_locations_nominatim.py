import sqlite3
import requests
import time
import sys

def resolve_nominatim(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
    headers = {'User-Agent': 'TelecomOutageMonitor/1.0 (Telia Repair Script)'}
    
    try:
        time.sleep(1.2) # Rate limit
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            addr = resp.json().get('address', {})
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality')
            if city:
                if ' kommun' in city:
                    city = city.replace(' kommun', '')
                return city
    except Exception as e:
        print(f"  Error: {e}")
    return None

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT o.id, o.incident_id, o.latitude, o.longitude, o.location
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'telia'
        AND o.latitude IS NOT NULL
        AND o.longitude IS NOT NULL
        AND o.latitude != 58.0
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} Telia incidents to consider for location upgrade.")
    
    updated = 0
    for row in rows:
        oid, inc_id, lat, lon, old_loc = row
        
        # Only update if it currently just shows a county or Unknown
        if 'län' in old_loc or 'Unknown' in old_loc or ',' not in old_loc:
            county = old_loc if 'län' in old_loc else ""
            if ',' in old_loc:
                county = old_loc.split(',')[1].strip()
            
            city = resolve_nominatim(lat, lon)
            if city:
                new_loc = f"{city}, {county}" if county else city
                # Don't duplicate if city == county
                if new_loc == f"{county}, {county}":
                    new_loc = county
                    
                print(f"[{inc_id}] {old_loc} -> {new_loc}")
                cur.execute("UPDATE outages SET location = ? WHERE id = ?", (new_loc, oid))
                updated += 1
                
                # Commit every 10 updates
                if updated % 10 == 0:
                    conn.commit()
    
    conn.commit()
    conn.close()
    print(f"Finished. Updated {updated} incidents.")

if __name__ == "__main__":
    main()
