import sqlite3
import time
from geopy.geocoders import Nominatim

def geocode_tre_missing():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    output_path = 'd:/94 FAH works/Telecom-Outage/tre_missing.txt'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch missing Tre incidents
    query = """
        SELECT o.incident_id, o.location 
        FROM outages o 
        JOIN operators op ON o.operator_id = op.id 
        WHERE op.name = 'tre' AND (o.latitude IS NULL OR o.longitude IS NULL)
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    # Get unique locations to minimize API calls
    unique_locations = set(r[1] for r in rows if r[1])
    print(f"Found {len(rows)} incidents across {len(unique_locations)} unique locations.")
    
    geolocator = Nominatim(user_agent="TreGeocode/1.0")
    location_map = {}
    
    print("Geocoding unique locations...")
    for loc in unique_locations:
        search_term = f"{loc}, Sweden"
        try:
            time.sleep(1.2) # Rate limit
            result = geolocator.geocode(search_term)
            if result:
                location_map[loc] = (result.latitude, result.longitude)
                print(f"  [OK] {loc} -> {result.latitude}, {result.longitude}")
            else:
                location_map[loc] = (None, None)
                print(f"  [FAIL] {loc} -> Not found")
        except Exception as e:
            location_map[loc] = (None, None)
            print(f"  [ERROR] {loc} -> {e}")
            
    # Write to text file
    print("Writing results to tre_missing.txt...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Proposed Geocoding for Tre Missing Coordinates\n")
        f.write(f"# Total Incidents: {len(rows)}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Incident ID':<15} | {'Location':<25} | {'Latitude':<12} | {'Longitude':<12}\n")
        f.write("-" * 80 + "\n")
        
        for inc_id, loc in rows:
            if not loc:
                lat, lon = "NULL", "NULL"
            else:
                coords = location_map.get(loc, (None, None))
                lat = f"{coords[0]:.6f}" if coords[0] is not None else "NULL"
                lon = f"{coords[1]:.6f}" if coords[1] is not None else "NULL"
                
            f.write(f"{inc_id:<15} | {loc:<25} | {lat:<12} | {lon:<12}\n")

    print(f"Finished. Check {output_path}")

if __name__ == "__main__":
    geocode_tre_missing()
