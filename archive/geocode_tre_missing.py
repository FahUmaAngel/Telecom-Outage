import sqlite3
import time
from geopy.geocoders import Nominatim

def _geocode_location(geolocator, loc):
    """Geocode a location and return (lat, lon) or (None, None)."""
    try:
        time.sleep(1.2)
        result = geolocator.geocode(f"{loc}, Sweden")
        if result:
            print(f"  [OK] {loc} -> {result.latitude}, {result.longitude}")
            return (result.latitude, result.longitude)
        print(f"  [FAIL] {loc} -> Not found")
        return (None, None)
    except Exception as e:
        print(f"  [ERROR] {loc} -> {e}")
        return (None, None)


def _format_coords(coords):
    """Format coordinates for output."""
    if coords[0] is not None:
        return f"{coords[0]:.6f}", f"{coords[1]:.6f}"
    return "NULL", "NULL"


def _write_results(output_path, rows, location_map):
    """Write geocoding results to file."""
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
                lat, lon = _format_coords(location_map.get(loc, (None, None)))
            f.write(f"{inc_id:<15} | {loc:<25} | {lat:<12} | {lon:<12}\n")


def geocode_tre_missing():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    output_path = 'd:/94 FAH works/Telecom-Outage/tre_missing.txt'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
        SELECT o.incident_id, o.location 
        FROM outages o 
        JOIN operators op ON o.operator_id = op.id 
        WHERE op.name = 'tre' AND (o.latitude IS NULL OR o.longitude IS NULL)
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    unique_locations = {r[1] for r in rows if r[1]}
    print(f"Found {len(rows)} incidents across {len(unique_locations)} unique locations.")
    
    geolocator = Nominatim(user_agent="TreGeocode/1.0")
    location_map = {}
    
    print("Geocoding unique locations...")
    for loc in unique_locations:
        location_map[loc] = _geocode_location(geolocator, loc)
    
    print("Writing results to tre_missing.txt...")
    _write_results(output_path, rows, location_map)
    print(f"Finished. Check {output_path}")

if __name__ == "__main__":
    geocode_tre_missing()
