import requests
import json
from datetime import datetime
import time

# Extract token from the portal
print("Fetching portal to get token...")
r = requests.get('https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage')
html = r.text
token = None
for line in html.split('\n'):
    if "var token =" in line or "__token__ =" in line or "token:" in line:
        try:
            token = line.split("'")[1]
            break
        except: pass

if not token:
    print("Could not find token in HTML.")
    # Look for it in iframe source
    iframe_src = None
    for line in html.split('\n'):
        if "<iframe" in line and "src=" in line:
            iframe_src = line.split('src="')[1].split('"')[0]
            break
            
    if iframe_src:
        r2 = requests.get(iframe_src)
        for line in r2.text.split('\n'):
            if "token:" in line or "token =" in line or "__token__ =" in line:
                try:
                    token = line.split("'")[1]
                    break
                except: pass

if not token:
    print("Still no token! Aborting.")
else:
    print(f"Got token: {token[:10]}...")
    
    # Try the API
    url = f"https://pebbles.teliasonera.net/pebbles/api/coverage2/GetFaultTimeline"
    
    payload = {
        "culture": "sv-SE",
        "dateRange": {
            "from": "2025-01-01T00:00:00",
            "to": "2025-01-31T23:59:59"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://coverage.ddc.teliasonera.net",
        "Referer": "https://coverage.ddc.teliasonera.net/"
    }
    
    print("Calling GetFaultTimeline for Jan 2025...")
    try:
        resp = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            events = data.get('events', [])
            print(f"Found {len(events)} events!")
            if events:
                print("First event preview:")
                print(json.dumps(events[0], indent=2)[:300])
        else:
            print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
