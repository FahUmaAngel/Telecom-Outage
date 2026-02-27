"""
In-browser scraper: uses Selenium to call Telia's AdminAreaList API
via jQuery.ajax() inside the live browser session (no auth issues).
Then extracts all current faults from the page HTML.
"""
import json
import re
import time
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
BASE = "/coverageportal_se"

SERVICES = "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE"

SWEDISH_COUNTIES = [
    "Stockholms", "Uppsala", "Södermanlands", "Östergötlands",
    "Jönköpings", "Kronobergs", "Kalmar", "Gotlands",
    "Blekinge", "Skåne", "Hallands", "Västra Götalands",
    "Värmlands", "Örebro", "Västmanlands", "Dalarnas",
    "Gävleborgs", "Västernorrlands", "Jämtlands",
    "Västerbottens", "Norrbottens"
]


def make_driver():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return webdriver.Chrome(options=opts)


def get_ert_token(driver):
    """Extract ert token from performance logs."""
    logs = driver.get_log('performance')
    for entry in logs:
        try:
            msg = json.loads(entry['message'])
            url = msg.get('message', {}).get('params', {}).get('request', {}).get('url', '')
            if 'ert=' in url and 'coverageportal' in url:
                m = re.search(r'\bert=([^&]+)', url)
                if m:
                    return m.group(1)
        except Exception:
            pass
    
    # Try from page source
    src = driver.page_source
    matches = re.findall(r'"ert"\s*:\s*"([^"]+)"', src)
    if matches:
        return matches[0]
    return None


def scrape():
    driver = make_driver()
    all_outages = []
    
    try:
        print("Loading Telia portal...")
        driver.get(PORTAL_URL)
        time.sleep(10)
        
        ert = get_ert_token(driver)
        print(f"ERT token: {'found' if ert else 'NOT FOUND'}")
        
        # === 1. Call AdminAreaList via in-browser jQuery ===
        if ert:
            js_call = f"""
            return new Promise((resolve) => {{
                $.ajax({{
                    url: '/coverageportal_se/Fault/AdminAreaList',
                    type: 'GET',
                    data: {{
                        services: '{SERVICES}',
                        faultsLastUpdated: '',
                        cacheKey: '',
                        ert: '{ert}'
                    }},
                    success: function(data) {{ resolve({{success: true, data: data}}); }},
                    error: function(err) {{ resolve({{success: false, error: err.status + ' ' + err.statusText}}); }}
                }});
            }});
            """
            
            try:
                result = driver.execute_async_script("""
                    var callback = arguments[arguments.length - 1];
                    $.ajax({
                        url: '/coverageportal_se/Fault/AdminAreaList',
                        type: 'GET',
                        data: {
                            services: '""" + SERVICES + """',
                            faultsLastUpdated: '',
                            cacheKey: '',
                            ert: '""" + ert + """'
                        },
                        success: function(data) { callback({success: true, data: data}); },
                        error: function(err) { callback({success: false, error: err.status}); }
                    });
                """)
                
                print(f"AdminAreaList result: {result}")
                
                if result and result.get('success') and result.get('data'):
                    data = result['data']
                    print(f"Data type: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                    
                    # Parse fault data
                    if isinstance(data, dict):
                        areas = data.get('AdminAreas', data.get('areas', []))
                    elif isinstance(data, list):
                        areas = data
                    else:
                        areas = []
                    
                    for area in areas:
                        area_name = area.get('Name', area.get('name', 'Unknown'))
                        faults = area.get('Faults', area.get('faults', []))
                        
                        for fault in faults:
                            inc_id = (
                                fault.get('IncidentId') or 
                                fault.get('Id') or 
                                fault.get('FaultId') or
                                f"TLI_{area_name}_{len(all_outages)}"
                            )
                            all_outages.append({
                                'incident_id': inc_id,
                                'operator': 'Telia',
                                'source': 'telia_ajax_api',
                                'status': 'active',
                                'location': area_name,
                                'description': str(fault.get('Description', '')),
                                'title': f"Telia fault in {area_name}",
                                'start_time': str(fault.get('StartTime', '')),
                                'estimated_end': str(fault.get('EndTime', ''))
                            })
                    
                    print(f"Extracted {len(all_outages)} faults from AdminAreaList")
                        
            except Exception as e:
                print(f"jQuery call error: {e}")
        
        # === 2. Extract from page HTML (current visible outages) ===
        print("\nExtracting from page HTML...")
        page_src = driver.page_source
        
        # Extract INCSE IDs
        incse_ids = set(re.findall(r'INCSE\d+', page_src))
        print(f"INCSE IDs in page: {incse_ids}")
        
        for inc_id in incse_ids:
            if not any(o['incident_id'] == inc_id for o in all_outages):
                # Find context around this ID
                idx = page_src.find(inc_id)
                context = page_src[max(0, idx-200):idx+500]
                
                # Try to find location
                location = None
                for county in SWEDISH_COUNTIES:
                    if county in context:
                        location = county + ' län'
                        break
                
                all_outages.append({
                    'incident_id': inc_id,
                    'operator': 'Telia',
                    'source': 'telia_page_html',
                    'status': 'active',
                    'location': location or 'Sverige',
                    'title': f"Incident {inc_id}",
                    'description': re.sub(r'<[^>]+>', ' ', context)[:300],
                })
        
        # === 3. Try to expand county links and get more incidents ===
        print("\nExpanding county links...")
        try:
            county_links = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
            print(f"Found {len(county_links)} county links")
            
            seen = {o['incident_id'] for o in all_outages}
            
            for i in range(len(county_links)):
                try:
                    links = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
                    if i >= len(links):
                        break
                    
                    link = links[i]
                    
                    # Get county name
                    try:
                        row = link.find_element(By.XPATH, "./ancestor::tr")
                        row_text = row.text
                        county = None
                        for c in SWEDISH_COUNTIES:
                            if c in row_text:
                                county = c + ' län'
                                break
                    except:
                        county = None
                    
                    driver.execute_script("arguments[0].click()", link)
                    time.sleep(3)
                    
                    src = driver.page_source
                    new_ids = set(re.findall(r'INCSE\d+', src)) - seen
                    
                    for inc_id in new_ids:
                        seen.add(inc_id)
                        all_outages.append({
                            'incident_id': inc_id,
                            'operator': 'Telia',
                            'source': 'telia_county_expand',
                            'status': 'active',
                            'location': county or 'Sverige',
                            'title': f"Incident {inc_id}",
                        })
                    
                    driver.back()
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"  County {i} error: {e}")
                    continue
        except Exception as e:
            print(f"County expand failed: {e}")
        
        print(f"\n✓ Total unique outages: {len(all_outages)}")
        
        result = {
            'outages': all_outages,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'source': 'in_browser_api'
        }
        
        with open('telia_inbrowser_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Saved to telia_inbrowser_results.json")
        return result
        
    finally:
        driver.quit()


if __name__ == '__main__':
    result = scrape()
    
    if result['outages']:
        print(f"\nSample outages:")
        for o in result['outages'][:3]:
            print(f"  {o['incident_id']} - {o['location']} - {o['status']}")
        
        # Now ingest
        print("\nIngesting into database...")
        from scrapers.common.geocoding import get_county_coordinates
        from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
        from scrapers.db.connection import get_db
        from scrapers.db.crud import save_outage
        
        db = next(get_db())
        saved = skipped = 0
        
        COUNTY_MAP = {c.replace(' ', '') + 'län': c + ' län' for c in [
            "Stockholms", "Uppsala", "Södermanlands", "Östergötlands",
            "Jönköpings", "Kronobergs", "Kalmar", "Gotlands",
            "Blekinge", "Skåne", "Hallands", "Västra Götalands",
            "Värmlands", "Örebro", "Västmanlands", "Dalarnas",
            "Gävleborgs", "Västernorrlands", "Jämtlands",
            "Västerbottens", "Norrbottens"
        ]}
        
        try:
            for outage in result['outages']:
                try:
                    inc_id = outage.get('incident_id')
                    if not inc_id:
                        continue
                    
                    location = outage.get('location', 'Sverige')
                    coords = None
                    for county in SWEDISH_COUNTIES:
                        if county in location:
                            coords = get_county_coordinates(county + ' län', jitter=True)
                            break
                    
                    normalized = NormalizedOutage(
                        operator=OperatorEnum.TELIA,
                        incident_id=inc_id,
                        title={'sv': outage.get('title', inc_id), 'en': outage.get('title', inc_id)},
                        description={'sv': outage.get('description', ''), 'en': outage.get('description', '')},
                        location=location,
                        status=OutageStatus.ACTIVE,
                        severity=SeverityLevel.MEDIUM,
                        affected_services=['mobile'],
                        source_url=PORTAL_URL,
                        started_at=None,
                        estimated_fix_time=None,
                        latitude=coords[0] if coords else None,
                        longitude=coords[1] if coords else None,
                    )
                    
                    save_outage(db, normalized, {'source': outage.get('source', 'telia')})
                    saved += 1
                    
                except Exception as e:
                    print(f"  Ingest error {outage.get('incident_id')}: {e}")
                    skipped += 1
            
            db.commit()
            print(f"✓ Ingested: {saved} saved, {skipped} skipped")
            
        finally:
            db.close()
    else:
        print("\nNo outages found to ingest.")
