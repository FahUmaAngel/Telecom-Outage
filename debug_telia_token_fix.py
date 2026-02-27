import requests
import re
import json

def debug_api_with_token():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    base = 'https://coverage.ddc.teliasonera.net/coverageportal_se'
    
    # 1. Get Token
    print("Fetching token...")
    r = s.get(f"{base}?appmode=outage")
    token = None
    m = re.search(r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', r.text)
    if m:
        token = m.group(1)
    
    print(f"Token: {token[:20]}..." if token else "Token: None")
    
    # 2. Try AdminAreaList WITH token in query
    url = f"{base}/Fault/AdminAreaList"
    params = {'ert': token} if token else {}
    print(f"Fetching areas from {url} with params {list(params.keys())}...")
    r_areas = s.get(url, params=params)
    print(f"Status: {r_areas.status_code}")
    print(f"Response: {r_areas.text[:500]}")
    
    if r_areas.status_code == 200 and r_areas.text.strip():
        try:
            areas = r_areas.json()
            print(f"SUCCESS! Found {len(areas)} areas")
        except:
            print("Failed to parse JSON")

if __name__ == "__main__":
    debug_api_with_token()
