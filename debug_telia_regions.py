import requests
import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_token(session, base_url):
    url = f"{base_url}?appmode=outage"
    resp = session.get(url, timeout=10)
    # Try all patterns from enghouse.py
    patterns = [
        r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']',
        r'value=["\']([^"\']+)["\']\s+id=["\']csrft["\']',
        r'[?&](?:ert|rt)=([^&#]+)',
        r'(?:ert|rt)["\']?\s*[:=]\s*["\']([^"\']+)["\']'
    ]
    for p in patterns:
        m = re.search(p, resp.text)
        if m:
            return m.group(1)
    return None

def debug_regions():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    base = 'https://coverage.ddc.teliasonera.net/coverageportal_se'
    
    token = get_token(s, base)
    print(f"Token: {token}")
    
    # Try getting areas
    r_areas = s.get(f"{base}/Fault/AdminAreaList")
    print(f"Areas Status: {r_areas.status_code}")
    if r_areas.status_code == 200:
        try:
            areas = r_areas.json()
            print(f"Found {len(areas)} areas")
            
            all_records = []
            for a in areas:
                name = a.get('Name')
                aid = a.get('Id')
                print(f"Fetching {name}...")
                r_faults = s.post(f"{base}/Fault/RegionFaultList", data={'regionId': aid, 'ert': token})
                if r_faults.status_code == 200:
                    faults = r_faults.json()
                    for f in faults:
                        f['RegionName'] = name
                        all_records.append(f)
                else:
                    print(f"  Failed {name}: {r_faults.status_code}")
            
            with open('telia_debug_all_regions.json', 'w', encoding='utf-8') as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(all_records)} records to telia_debug_all_regions.json")
            
        except Exception as e:
            print(f"Error: {e}")
            print(f"Raw Areas Response: {r_areas.text[:200]}")

if __name__ == "__main__":
    debug_regions()
