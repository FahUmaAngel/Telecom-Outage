import sqlite3
import random
from openlocationcode import openlocationcode as olc

def apply_jitter_tre():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Coordinate mapping for the 20 unique locations we found earlier
    # (Matches the results from geocode_tre_missing_plus.py)
    location_base_coords = {
        'Dalarnas län': (61.0603779, 14.2151224),
        'Västerbottens län': (64.7282044, 18.5534514),
        'Blekinge län': (56.1240605, 15.4023088),
        'Stockholms län': (59.3948653, 18.6660073),
        'Kronobergs län': (56.8007878, 14.410897),
        'Södermanlands län': (58.9649445, 16.7293984),
        'Västra Götalands län': (58.2245513, 12.6522185),
        'Skåne län': (55.8472301, 13.6339292),
        'Västmanlands län': (59.6965564, 16.1846084),
        'Hallands län': (56.9547859, 12.8565682),
        'Sverige': (59.6749712, 14.5208584),
        'Västernorrlands län': (63.0478258, 18.1014438),
        'Örebro län': (59.3784871, 14.988292),
        'Kalmar län': (57.0262661, 16.5749837),
        'Jämtlands län': (63.3465856, 14.1237511),
        'Gävleborgs län': (61.2682236, 16.688925),
        'Östergötlands län': (58.3678117, 16.0463853),
        'Norrbottens län': (66.9812104, 19.9991639),
        'Värmlands län': (59.8907917, 13.2949215),
        'Uppsala län': (60.0, 17.5) # Fallback for Uppsala if found
    }

    # 2. Fetch the 171 incidents
    query = """
        SELECT o.id, o.location 
        FROM outages o 
        JOIN operators op ON o.operator_id = op.id 
        WHERE op.name = 'tre' AND (o.latitude IS NULL OR (o.latitude IN (59.3948653, 59.6749712)))
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Applying jitter to {len(rows)} Tre incidents...")
    
    updated_count = 0
    for db_id, loc in rows:
        base = location_base_coords.get(loc)
        if not base and loc == 'Sverige':
            base = location_base_coords['Sverige']
        
        if base:
            # Apply jitter: +/- 0.005 to 0.015 degrees (~500m to 1.5km)
            # We want them visible but distinct
            lat_jitter = random.uniform(-0.012, 0.012)
            lon_jitter = random.uniform(-0.012, 0.012)
            
            final_lat = base[0] + lat_jitter
            final_lon = base[1] + lon_jitter
            
            # Encode Plus Code
            plus_code = olc.encode(final_lat, final_lon)
            
            cursor.execute("""
                UPDATE outages 
                SET latitude = ?, longitude = ?, place = ? 
                WHERE id = ?
            """, (final_lat, final_lon, plus_code, db_id))
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"Updated {updated_count} incidents with unique jittered coordinates and Plus Codes.")

if __name__ == "__main__":
    apply_jitter_tre()
