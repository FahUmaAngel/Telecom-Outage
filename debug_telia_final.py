import requests
import re

def final_debug():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    base = 'https://coverage.ddc.teliasonera.net/coverageportal_se'
    
    # 1. Get Token
    r = s.get(f"{base}?appmode=outage")
    token = None
    patterns = [r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', r'ert=([^&#"]+)']
    for p in patterns:
        m = re.search(p, r.text)
        if m:
            token = m.group(1)
            break
    
    print(f"Token: {token}")
    
    # 2. Get Areas with Token
    url = f"{base}/Fault/AdminAreaList"
    params = {'ert': token} if token else {}
    r_areas = s.get(url, params=params)
    print(f"URL: {r_areas.url}")
    print(f"Status: {r_areas.status_code}")
    print(f"Response (first 500 chars): {r_areas.text[:500]}")
    
    if r_areas.status_code == 200 and r_areas.text.strip():
        try:
            areas = r_areas.json()
            print(f"Found {len(areas)} areas")
            area = areas[0]
            print(f"First Area: {area}")
            
            # 3. Get Faults for first area
            r_faults = s.post(f"{base}/Fault/RegionFaultList", data={'regionId': area['Id'], 'ert': token})
            print(f"Faults Status: {r_faults.status_code}")
            print(f"Faults Response: {r_faults.text[:500]}")
        except Exception as e:
            print(f"JSON Error: {e}")

if __name__ == "__main__":
    final_debug()
