import sqlite3
import requests
import time

def resolve_nominatim(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
    headers = {'User-Agent': 'TelecomOutageMonitor/1.0 (Telia Final Repair Script)'}
    
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
    
    # Get Telia incidents that are just 'Unknown' but have valid coordinates
    cur.execute("""
        SELECT o.id, o.incident_id, o.latitude, o.longitude
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'telia'
        AND o.location = 'Unknown'
        AND o.latitude IS NOT NULL
        AND o.longitude IS NOT NULL
        AND o.latitude != 58.0
    """)
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} 'Unknown' incidents to resolve via coordinates.")
    
    updated = 0
    for row in rows:
        oid, inc_id, lat, lon = row
        
        city = resolve_nominatim(lat, lon)
        if city:
            print(f"[{inc_id}] Unknown -> {city}")
            cur.execute("UPDATE outages SET location = ? WHERE id = ?", (city, oid))
            updated += 1
            if updated % 5 == 0:
                conn.commit()
        else:
            print(f"[{inc_id}] Nominatim failed to find a city for {lat}, {lon}")
            
    conn.commit()
    conn.close()
    print(f"Finished. Resolved and updated {updated} incidents.")

if __name__ == "__main__":
    main()
