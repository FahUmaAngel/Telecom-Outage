import sqlite3
import time
from geopy.geocoders import Nominatim
from openlocationcode import openlocationcode as olc

def _geocode_location(geolocator, loc):
    """Geocode a location and return (lat, lon, plus_code) or (None, None, None)."""
    try:
        time.sleep(1.2)
        result = geolocator.geocode(f"{loc}, Sweden")
        if result:
            lat, lon = result.latitude, result.longitude
            plus_code = olc.encode(lat, lon)
            print(f"  [OK] {loc} -> {lat}, {lon} | {plus_code}")
            return (lat, lon, plus_code)
        print(f"  [FAIL] {loc} -> Not found")
        return (None, None, None)
    except Exception as e:
        print(f"  [ERROR] {loc} -> {e}")
        return (None, None, None)


def _format_location(loc, location_map):
    """Format location data for output."""
    if not loc:
        return "NULL", "NULL", "NULL"
    coords = location_map.get(loc, (None, None, None))
    lat = f"{coords[0]:.6f}" if coords[0] is not None else "NULL"
    lon = f"{coords[1]:.6f}" if coords[1] is not None else "NULL"
    pc = coords[2] if coords[2] is not None else "NULL"
    return lat, lon, pc


def _write_results(output_path, rows, location_map):
    """Write geocoding results to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Proposed Geocoding for Tre Missing Coordinates\n")
        f.write(f"# Total Incidents: {len(rows)}\n")
        f.write("-" * 100 + "\n")
        f.write(f"{'Incident ID':<15} | {'Location':<25} | {'Latitude':<12} | {'Longitude':<12} | {'Plus Code':<15}\n")
        f.write("-" * 100 + "\n")
        for inc_id, loc in rows:
            lat, lon, pc = _format_location(loc, location_map)
            f.write(f"{inc_id:<15} | {loc:<25} | {lat:<12} | {lon:<12} | {pc:<15}\n")


def geocode_tre_missing_with_pluscode():
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
    
    geolocator = Nominatim(user_agent="TreGeocode/2.0")
    location_map = {}
    
    print("Geocoding unique locations...")
    for loc in unique_locations:
        location_map[loc] = _geocode_location(geolocator, loc)
    
    _write_results(output_path, rows, location_map)
    print(f"Finished. Check {output_path}")

if __name__ == "__main__":
    geocode_tre_missing_with_pluscode()
