import sqlite3
import sys
import os

# Add to path to use geocoding
sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

VALID_COUNTIES = [
    "Stockholms län",
    "Södermanlands län",
    "Örebro län",
    "Jämtlands län",
    "Gävleborgs län",
    "Dalarnas län",
    "Västernorrland län",
    "Värmlands län",
    "Norrbottens län",
    "Västerbottens län",
    "Västra Götalands län",
    "Hallands län",
    "Östergötlands län",
    "Kalmar län",
    "Västmanlands län"
]

def verify_and_correct_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Correct INCSE0475544 and INCSE0476740
    ids_to_fix = ['INCSE0475544', 'INCSE0476740']
    correct_location = "Västra Götalands län"
    coords = get_county_coordinates(correct_location, jitter=True)
    
    for inc_id in ids_to_fix:
        cursor.execute("""
            UPDATE outages
            SET location = ?, latitude = ?, longitude = ?
            WHERE incident_id = ? AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
        """, (correct_location, coords[0] if coords else 58.0, coords[1] if coords else 13.0, inc_id))
        print(f"Corrected {inc_id} to {correct_location}")
    
    conn.commit()
    
    # 2. Check all Telia locations for invalid ones
    cursor.execute("""
        SELECT DISTINCT location 
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'telia')
    """)
    rows = cursor.fetchall()
    
    print("\n--- Telia Locations in DB ---")
    invalid_locations = []
    for row in rows:
        loc = row[0]
        if loc not in VALID_COUNTIES:
            invalid_locations.append(loc)
        print(loc)
        
    print("\n--- Invalid / Unlisted Locations ---")
    for loc in invalid_locations:
        print(loc)

    conn.close()

if __name__ == "__main__":
    verify_and_correct_locations()
