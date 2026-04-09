"""
Debug the GetLocationInfo response to find where city/municipality info is stored.
"""
import requests
import json
import re
import urllib.parse
from playwright.sync_api import sync_playwright

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
SERVICES = "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE"

# Known coordinates for incidents
TEST_INCIDENTS = [
    ("INCSE0425201", 59.3360861, 18.0718987, "Stockholms län"),
    ("INCSE0399811", 58.78386, 15.07324, "Unknown")  
]

# Get token via quick Playwright session
token = None
fault_cache_keys = ""
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    captured = {}
    
    def on_resp(r):
        global token, fault_cache_keys
        if "coverageportal" in r.url and r.status == 200:
            ert = re.search(r'ert=([^&]+)', r.url)
            if ert and not token:
                token = urllib.parse.unquote(ert.group(1))
            try:
                if "FaultsLastUpdated" in r.url:
                    d = r.json()
                    ck = d.get("ActiveCacheKey","")
                    pk = d.get("PlannedCacheKey","")
                    if ck:
                        fault_cache_keys = f"PW,{pk},16|AF,{ck},2"
            except: pass
    
    page.on("response", on_resp)
    page.goto(f"{BASE_URL}?appmode=outage", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    browser.close()

print(f"Token: {'Found' if token else 'Not found'}")
print(f"Fault cache keys: {fault_cache_keys[:50]}")

if not token:
    print("Cannot continue without token")
    exit(1)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": BASE_URL})

for inc_id, lat, lon, expected_loc in TEST_INCIDENTS:
    print(f"\n{'='*60}")
    print(f"Incident: {inc_id} (expected: {expected_loc})")
    print(f"Coords: lat={lat}, lon={lon}")
    
    params = {
        "northing": round(lat, 5),
        "easting": round(lon, 5),
        "services": SERVICES,
        "covQuality": 1,
        "faultCacheKeys": fault_cache_keys,
        "ert": token
    }
    
    resp = session.get(f"{BASE_URL}/Outage/GetLocationInfo", params=params, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        # Print FULL response to see all available fields
        print(json.dumps(data, indent=2, ensure_ascii=False))
