"""
Test the Outage/GetLocationInfo API endpoint discovered in Phase 1.
This endpoint takes lat/lng and returns location info including service and coverage data.
"""
import requests
import json
import sqlite3
import urllib.parse

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
SERVICES = "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": BASE_URL,
    "Accept": "application/json, text/plain, */*"
})

# Step 1: Get the session token first
print("Getting session token...")
resp = session.get(f"{BASE_URL}?appmode=outage", timeout=30)
import re
token_match = re.search(r"ert=([^&\"']+)", resp.text)
if token_match:
    token = urllib.parse.unquote(token_match.group(1))
    print(f"Found token: {token[:40]}...")
else:
    token = None
    print("No token found, trying without")

# Step 2: Get an incident with coordinates from the database
conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("""
    SELECT incident_id, latitude, longitude, location 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'telia' 
    AND incident_id IS NOT NULL 
    AND latitude IS NOT NULL 
    AND latitude NOT IN (58.0)
    LIMIT 5
""")
rows = cur.fetchall()
conn.close()

print(f"\nFound {len(rows)} Telia incidents with coordinates:")
for r in rows:
    print(f"  {r[0]}: lat={r[1]}, lon={r[2]}, location={r[3]}")

if rows:
    # Test GetLocationInfo for the first one
    inc_id, lat, lon, loc = rows[0]
    print(f"\n--- Testing GetLocationInfo for {inc_id} (lat={lat}, lon={lon}) ---")
    
    params = {
        "northing": lat,
        "easting": lon,
        "services": SERVICES,
        "covQuality": 1
    }
    if token:
        params["ert"] = token
    
    url = f"{BASE_URL}/Outage/GetLocationInfo"
    resp = session.get(url, params=params, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
        except:
            print(f"Raw: {resp.text[:300]}")
    else:
        print(f"Error: {resp.text[:300]}")

# Step 3: Also try the Fault/TicketSearch endpoint (search by incident ID)
if rows:
    inc_id = rows[0][0]
    print(f"\n--- Testing Fault/TicketSearch for {inc_id} ---")
    for endpoint in [
        f"{BASE_URL}/Fault/TicketDetail",
        f"{BASE_URL}/Fault/TicketSearch",
        f"{BASE_URL}/Fault/IncidentInfo",
    ]:
        try:
            params = {"externalId": inc_id, "incidentId": inc_id}
            if token:
                params["ert"] = token
            resp = session.get(endpoint, params=params, timeout=10)
            print(f"  {endpoint.split('/')[-1]}: status={resp.status_code}, body={resp.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
