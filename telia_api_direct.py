"""
Directly call Telia's AdminAreaList API using the captured session token.
This gets live fault data per administrative region.
Then calls the NetworkEventsTimeline endpoint for historical data.
"""
import json
import re
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
BASE = "https://coverage.ddc.teliasonera.net/coverageportal_se"

SERVICES = "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE"

def get_session_token(driver):
    """Extract the 'ert' session token from the page's network requests."""
    logs = driver.get_log('performance')
    for entry in logs:
        try:
            msg = json.loads(entry['message'])
            url = msg.get('message', {}).get('params', {}).get('request', {}).get('url', '')
            if 'ert=' in url and 'coverageportal' in url:
                m = re.search(r'ert=([^&]+)', url)
                if m:
                    return m.group(1)
        except Exception:
            pass
    return None

def get_cookies(driver):
    """Get cookies as dict from driver."""
    return {c['name']: c['value'] for c in driver.get_cookies()}

def scrape_all_faults():
    """Full scrape using direct API calls."""
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=opts)
    all_outages = []
    
    try:
        print(f"Loading portal...")
        driver.get(PORTAL_URL)
        time.sleep(10)
        
        # Extract ERT token
        ert = get_session_token(driver)
        if not ert:
            print("WARNING: Could not extract ERT token, trying page source...")
            src = driver.page_source
            m = re.search(r'ert["\']?\s*[:=]\s*["\']([^"\']+)', src)
            if m:
                ert = m.group(1)
        
        if not ert:
            print("ERROR: Could not find ERT token!")
        else:
            print(f"✓ ERT token: {ert[:50]}...")
        
        cookies = get_cookies(driver)
        print(f"Cookies: {list(cookies.keys())}")
        
        headers = {
            'Accept': '*/*',
            'Referer': PORTAL_URL,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'X-KL-Ajax-Request': 'Ajax_Request',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        results = {'outages': [], 'timestamp': datetime.now().isoformat(), 'success': False}
        
        # 1. GET AdminAreaList - live faults by region
        admin_url = f"{BASE}/Fault/AdminAreaList"
        params = {
            'services': SERVICES,
            'faultsLastUpdated': '',
            'cacheKey': '',
        }
        if ert:
            params['ert'] = ert
        
        print(f"\nCalling AdminAreaList...")
        try:
            r = requests.get(admin_url, params=params, headers=headers, cookies=cookies, timeout=20)
            print(f"Status: {r.status_code}, Size: {len(r.text)} chars")
            print(f"Response preview: {r.text[:500]}")
            
            if r.status_code == 200 and r.text.strip():
                try:
                    data = r.json()
                    print(f"JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    # Navigate the response structure
                    if isinstance(data, dict):
                        admin_areas = data.get('AdminAreas', data.get('areas', data.get('faults', [])))
                    elif isinstance(data, list):
                        admin_areas = data
                    else:
                        admin_areas = []
                    
                    print(f"Admin areas: {len(admin_areas)}")
                    
                    for area in admin_areas:
                        name = area.get('Name', area.get('name', 'Unknown'))
                        faults = area.get('Faults', area.get('faults', []))
                        print(f"  {name}: {len(faults)} faults")
                        
                        for fault in faults:
                            inc_id = fault.get('IncidentId', fault.get('id', fault.get('FaultId', '')))
                            if not inc_id:
                                # Try to find any ID-like field
                                for k, v in fault.items():
                                    if 'id' in k.lower() or 'inc' in k.lower():
                                        inc_id = str(v)
                                        break
                            
                            results['outages'].append({
                                'incident_id': inc_id or f"TLI_{name}_{len(results['outages'])}",
                                'operator': 'Telia',
                                'source': 'telia_admin_area_api',
                                'status': 'active',
                                'location': name,
                                'description': str(fault)[:200],
                                'title': f"Fault in {name}",
                                'start_time': fault.get('StartTime', fault.get('startTime', '')),
                                'estimated_end': fault.get('EndTime', fault.get('endTime', '')),
                                'raw': fault
                            })
                except json.JSONDecodeError:
                    # Try XML or HTML parsing
                    print("Not JSON, trying regex...")
                    inc_ids = set(re.findall(r'INCSE\d+', r.text))
                    for inc_id in inc_ids:
                        results['outages'].append({
                            'incident_id': inc_id,
                            'operator': 'Telia',
                            'source': 'telia_admin_area_regex',
                            'status': 'active'
                        })
        except Exception as e:
            print(f"AdminAreaList error: {e}")
        
        # 2. GET NetworkEventsTimeline - historical events
        timeline_url = f"{BASE}/NetworkEventsTimeline/Content/Script"
        print(f"\nCalling NetworkEventsTimeline script...")
        try:
            r2 = requests.get(timeline_url, headers=headers, cookies=cookies, timeout=20)
            print(f"Status: {r2.status_code}, Size: {len(r2.text)} chars")
            print(f"Preview: {r2.text[:300]}")
        except Exception as e:
            print(f"Timeline script error: {e}")
        
        # 3. Try the history-specific endpoint
        history_urls = [
            f"{BASE}/Fault/GetFaultTimeline",
            f"{BASE}/NetworkEventsTimeline/GetEvents",
            f"{BASE}/Fault/GetHistoricalFaults",
            f"{BASE}/Outage/GetHistory",
        ]
        
        for url in history_urls:
            print(f"\nTrying: {url}")
            try:
                r3 = requests.get(url, headers=headers, cookies=cookies, timeout=10)
                print(f"  Status: {r3.status_code}, Size: {len(r3.text)}")
                if r3.status_code == 200 and len(r3.text) > 100:
                    print(f"  Preview: {r3.text[:300]}")
            except Exception as e:
                print(f"  Error: {e}")
        
        results['success'] = True
        print(f"\nTotal outages collected: {len(results['outages'])}")
        
        with open('telia_api_direct_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print("✓ Saved to telia_api_direct_results.json")
        
        return results
        
    finally:
        driver.quit()


if __name__ == '__main__':
    scrape_all_faults()
