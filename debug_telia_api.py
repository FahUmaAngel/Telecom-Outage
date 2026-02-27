import requests
import json
import re

def get_telia_sample():
    s = requests.Session()
    base = 'https://coverage.ddc.teliasonera.net/coverageportal_se'
    
    # 1. Get Token
    r = s.get(f'{base}?appmode=outage')
    m = re.search(r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', r.text)
    token = m.group(1) if m else None
    print(f"Token: {token}")
    
    # 2. Get Areas
    r_areas = s.get(f'{base}/Fault/AdminAreaList')
    if r_areas.status_code != 200:
        print(f"Failed to get areas: {r_areas.status_code}")
        return
    
    areas = r_areas.json()
    print(f"Found {len(areas)} areas")
    
    # 3. Get Faults for each area
    results = {}
    for area in areas[:5]: # Check first 5 areas
        name = area.get('Name')
        aid = area.get('Id')
        print(f"Fetching faults for {name} (ID: {aid})...")
        
        r_faults = s.post(f'{base}/Fault/RegionFaultList', data={'regionId': aid, 'ert': token})
        if r_faults.status_code == 200:
            try:
                faults = r_faults.json()
                results[name] = faults
                print(f"  Found {len(faults)} faults")
            except:
                print(f"  Failed to parse JSON for {name}")
        else:
            print(f"  Error: {r_faults.status_code}")
            
    with open('telia_api_debug_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    get_telia_sample()
