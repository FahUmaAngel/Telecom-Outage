import sqlite3
import json

# Regions in DB
# (1, 'Stockholms län')
# (2, 'Västra Götalands län')
# (3, 'Skåne län')
# (4, 'Uppsala län')
# (5, 'Östergötlands län')
# (6, 'Jönköpings län')
# (7, 'Kronobergs län')
# (8, 'Kalmar län')
# (9, 'Gotlands län')
# (10, 'Blekinge län')
# (11, 'Hallands län')
# (12, 'Värmlands län')
# (13, 'Örebro län')
# (14, 'Västmanlands län')
# (15, 'Dalarnas län')
# (16, 'Gävleborgs län')
# (17, 'Västernorrlands län')
# (18, 'Jämtlands län')
# (19, 'Västerbottens län')
# (20, 'Norrbottens län')
# (21, 'Södermanlands län')

REGION_MAP = {
    'Stockholms län': 1, 'Västra Götalands län': 2, 'Skåne län': 3,
    'Uppsala län': 4, 'Östergötlands län': 5, 'Jönköpings län': 6,
    'Kronobergs län': 7, 'Kalmar län': 8, 'Gotlands län': 9,
    'Blekinge län': 10, 'Hallands län': 11, 'Värmlands län': 12,
    'Örebro län': 13, 'Västmanlands län': 14, 'Dalarnas län': 15,
    'Gävleborgs län': 16, 'Västernorrlands län': 17, 'Jämtlands län': 18,
    'Västerbottens län': 19, 'Norrbottens län': 20, 'Södermanlands län': 21
}

# Simplified CITY_TO_COUNTY from translation.py
CITY_TO_COUNTY = {
    "Stockholm": "Stockholms län", "Göteborg": "Västra Götalands län", "Malmö": "Skåne län",
    "Uppsala": "Uppsala län", "Västerås": "Västmanlands län", "Örebro": "Örebro län",
    "Linköping": "Östergötlands län", "Helsingborg": "Skåne län", "Jönköping": "Jönköpings län",
    "Norrköping": "Östergötlands län", "Lund": "Skåne län", "Umeå": "Västerbottens län",
    "Gävle": "Gävleborgs län", "Borås": "Västra Götalands län", "Södertälje": "Stockholms län",
    "Varberg": "Hallands län", "Eskilstuna": "Södermanlands län", "Falun": "Dalarnas län",
    "Halmstad": "Hallands län", "Karlstad": "Värmlands län", "Växjö": "Kronobergs län",
    "Luleå": "Norrbottens län"
}

def normalize_location(loc_str):
    if not loc_str: return None
    
    # 1. Exact match with region
    for county in REGION_MAP.keys():
        if county.lower() in loc_str.lower():
            return county
            
    # 2. Check for "City, County"
    if "," in loc_str:
        parts = loc_str.split(",")
        county_part = parts[-1].strip()
        for county in REGION_MAP.keys():
            if county.lower() == county_part.lower():
                return county
                
    # 3. Check for City match
    for city, county in CITY_TO_COUNTY.items():
        if city.lower() in loc_str.lower():
            return county
            
    return None

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("SELECT id, incident_id, location, region_id FROM outages")
    rows = cur.fetchall()
    
    print(f"Checking {len(rows)} incidents...")
    updated_count = 0
    
    for row in rows:
        oid, inc_id, loc_str, current_rid = row
        
        region_name = normalize_location(loc_str)
        
        if region_name:
            rid = REGION_MAP[region_name]
            if loc_str != region_name or current_rid != rid:
                print(f"[{inc_id}] '{loc_str}' -> '{region_name}' (RID: {rid})")
                cur.execute("UPDATE outages SET location = ?, region_id = ? WHERE id = ?", (region_name, rid, oid))
                updated_count += 1
        
    conn.commit()
    conn.close()
    print(f"\nFinished. Updated {updated_count} incidents.")

if __name__ == "__main__":
    main()
