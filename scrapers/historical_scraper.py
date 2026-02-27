"""
Telia Historical Scraper - 2025-2026
Uses Selenium to navigate Telia's 'Nätverkshistorik' feature
and extract INCSE incident IDs for a date range.
"""
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import (
        StaleElementReferenceException, TimeoutException, NoSuchElementException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TeliaHistorical")

COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]


def get_chrome_driver():
    """Set up a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def extract_incidents_from_source(page_source: str, location: str = None) -> List[Dict]:
    """Extract INCSE incidents from page source."""
    incidents = []
    soup = BeautifulSoup(page_source, 'html.parser')
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 4:
            id_cell = cells[0].get_text(strip=True)
            if 'INCSE' in id_cell:
                inc_id_match = re.search(r'INCSE\d+', id_cell)
                if not inc_id_match:
                    continue
                inc_id = inc_id_match.group(0)
                
                desc = cells[1].get_text(strip=True).replace('Beskrivning', '').strip()
                start = cells[2].get_text(strip=True).replace('Starttid', '').strip()
                end = cells[3].get_text(strip=True).replace('Sluttid', '').strip()
                
                incidents.append({
                    'incident_id': inc_id,
                    'operator': 'Telia',
                    'source': 'telia_history',
                    'status': 'resolved',  # Historical = resolved
                    'description': desc,
                    'location': location or 'Sverige',
                    'start_time': start,
                    'estimated_end': end,
                    'title': f"Incident {inc_id}"
                })
    
    # Fallback: regex
    if not incidents:
        for inc_id in set(re.findall(r'INCSE\d+', page_source)):
            incidents.append({
                'incident_id': inc_id,
                'operator': 'Telia',
                'source': 'telia_history_regex',
                'status': 'resolved',
                'location': location or 'Sverige',
                'title': f"Incident {inc_id}"
            })
    
    return incidents


def set_date_and_get_incidents(driver, wait, target_date: str, month_str: str, year_str: str) -> List[Dict]:
    """
    Attempt to set the Nätverkshistorik date and scrape incidents.
    target_date: 'YYYY-MM-DD' string
    month_str: e.g. 'Februari'
    year_str: e.g. '2025'
    """
    all_incidents = []
    
    try:
        # Click 'Nätverkshistorik' radio
        try:
            hist_radio = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(., 'Nätverkshistorik')]")
            ))
            hist_radio.click()
            time.sleep(2)
            logger.info("✓ Clicked Nätverkshistorik")
        except TimeoutException:
            logger.warning("Could not find Nätverkshistorik radio button")
            return []
        
        # Look for date input
        try:
            date_input = driver.find_element(By.XPATH, "//input[@type='text' or contains(@class, 'date')]")
            date_input.clear()
            date_input.send_keys(target_date)
            time.sleep(1)
        except NoSuchElementException:
            pass
        
        # Click calendar icon 
        try:
            cal_icon = driver.find_element(By.XPATH, "//button[contains(@class,'calendar') or contains(@class, 'datepicker')]")
            cal_icon.click()
            time.sleep(1)
        except NoSuchElementException:
            pass
        
        time.sleep(3)
        
        # Extract incidents from current page source (after setting date)
        page_source = driver.page_source
        initial = extract_incidents_from_source(page_source)
        if initial:
            logger.info(f"Found {len(initial)} incidents for {target_date}")
        all_incidents.extend(initial)
        
        # Try to expand counties
        for county in SWEDISH_COUNTIES:
            try:
                county_links = driver.find_elements(By.XPATH, f"//a[contains(text(), '{county}')] | //td[contains(text(), '{county}')]")
                for link in county_links:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        link.click()
                        time.sleep(2)
                        county_page = driver.page_source
                        county_incidents = extract_incidents_from_source(county_page, location=county)
                        all_incidents.extend([i for i in county_incidents if i['incident_id'] not in [x['incident_id'] for x in all_incidents]])
                        driver.back()
                        time.sleep(1)
                        break
                    except Exception:
                        pass
            except Exception:
                pass
        
        return all_incidents
        
    except Exception as e:
        logger.error(f"Error extracting for {target_date}: {e}")
        return []


def scrape_telia_history(start_date: datetime, end_date: datetime) -> Dict:
    """
    Scrape Telia historical incidents between two dates.
    Samples once per week to avoid too many requests.
    """
    if not SELENIUM_AVAILABLE:
        return {'success': False, 'error': 'Selenium not available', 'outages': []}
    
    logger.info(f"Scraping Telia history from {start_date.date()} to {end_date.date()}")
    
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'date_range': f"{start_date.date()} to {end_date.date()}"
    }
    
    all_incident_ids = set()
    driver = None
    
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 15)
        
        # Load the portal
        logger.info(f"Loading: {COVERAGE_PORTAL_URL}")
        driver.get(COVERAGE_PORTAL_URL)
        time.sleep(6)
        
        # Click Nätverksstatus tab first
        try:
            status_tab = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(), 'Nätverksstatus')] | //div[contains(text(), 'Nätverksstatus')]")
            ))
            status_tab.click()
            time.sleep(3)
        except TimeoutException:
            logger.info("Already on Nätverksstatus tab or not found separately")
        
        # First scrape current active incidents
        logger.info("Scraping current active incidents first...")
        page_source = driver.page_source
        current_incidents = extract_incidents_from_source(page_source)
        for inc in current_incidents:
            inc['status'] = 'active'
            if inc['incident_id'] not in all_incident_ids:
                all_incident_ids.add(inc['incident_id'])
                results['outages'].append(inc)
        logger.info(f"Found {len(current_incidents)} current incidents")
        
        # Try to expand each county for current incidents
        try:
            county_rows = driver.find_elements(By.XPATH, "//a[contains(text(), 'Visa område')]")
            logger.info(f"Found {len(county_rows)} county links")
            
            for i in range(min(len(county_rows), 25)):
                try:
                    county_rows = driver.find_elements(By.XPATH, "//a[contains(text(), 'Visa område')]")
                    if i >= len(county_rows):
                        break
                    
                    row = county_rows[i]
                    # Get county name from parent
                    try:
                        parent_text = row.find_element(By.XPATH, "./ancestor::tr").text
                        county_name = None
                        for c in SWEDISH_COUNTIES:
                            if c.replace(' län', '') in parent_text:
                                county_name = c
                                break
                    except Exception:
                        county_name = None
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", row)
                    time.sleep(0.5)
                    row.click()
                    time.sleep(4)
                    
                    county_source = driver.page_source
                    county_incs = extract_incidents_from_source(county_source, location=county_name)
                    new = [inc for inc in county_incs if inc['incident_id'] not in all_incident_ids]
                    for inc in new:
                        all_incident_ids.add(inc['incident_id'])
                        results['outages'].append(inc)
                    
                    driver.back()
                    time.sleep(2)
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.warning(f"Error on county {i}: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Could not expand counties: {e}")
        
        # Now try historical data
        logger.info("Switching to historical mode...")
        try:
            # Reload the page to get a clean state
            driver.get(COVERAGE_PORTAL_URL)
            time.sleep(5)
            
            # Click Nätverksstatus tab
            try:
                tabs = driver.find_elements(By.XPATH, "//a[contains(@href, 'outage')] | //li[@class='nav-item']//a")
                for tab in tabs:
                    if 'Nätverksstatus' in tab.text:
                        tab.click()
                        time.sleep(2)
                        break
            except Exception:
                pass
            
            # Select Nätverkshistorik radio button
            hist_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'historik') or contains(text(), 'Historik')]")
            hist_clicked = False
            for elem in hist_elements:
                try:
                    parent = elem.find_element(By.XPATH, "./ancestor::label | ./ancestor::div[contains(@class,'radio')]")
                    parent.click()
                    hist_clicked = True
                    logger.info(f"✓ Clicked historik via parent: {elem.text}")
                    time.sleep(2)
                    break
                except Exception:
                    try:
                        elem.click()
                        hist_clicked = True
                        logger.info(f"✓ Clicked historik element: {elem.text}")
                        time.sleep(2)
                        break
                    except Exception:
                        pass
            
            if hist_clicked:
                # Look for date input and set a date
                date_inputs = driver.find_elements(By.XPATH, "//input[@type='date' or @type='text' and @placeholder]")
                for di in date_inputs:
                    try:
                        placeholder = di.get_attribute('placeholder')
                        if placeholder and 'datum' in placeholder.lower():
                            # Set date to start of 2025
                            di.clear()
                            di.send_keys("2025-01-01")
                            time.sleep(3)
                            
                            hist_page = driver.page_source
                            hist_incidents = extract_incidents_from_source(hist_page)
                            logger.info(f"Historical mode: found {len(hist_incidents)} incidents for 2025-01-01")
                            for inc in hist_incidents:
                                if inc['incident_id'] not in all_incident_ids:
                                    all_incident_ids.add(inc['incident_id'])
                                    results['outages'].append(inc)
                            break
                    except Exception as e:
                        logger.warning(f"Date input error: {e}")
            
        except Exception as e:
            logger.warning(f"Historical mode failed: {e}")
        
        results['success'] = True
        logger.info(f"Total unique incidents collected: {len(results['outages'])}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        results['error'] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return results


def scrape_telenor_current() -> Dict:
    """Scrape current Telenor incidents using requests."""
    import requests
    from bs4 import BeautifulSoup
    
    logger.info("Scraping Telenor current disruptions...")
    
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'sv-SE,sv;q=0.9',
    }
    
    try:
        response = requests.get(
            'https://www.telenor.se/kundservice/driftinformation/',
            headers=headers,
            timeout=15
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        incident_count = 0
        # Look for disruption articles/cards
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(
            kw in str(x).lower() for kw in ['incident', 'outage', 'disturbance', 'fault', 'storning', 'driftinformation', 'card']
        ))
        
        for art in articles:
            text = art.get_text(strip=True)
            if len(text) > 20:
                inc_id = f"TNR{datetime.now().strftime('%Y%m%d')}{incident_count:03d}"
                incident_count += 1
                
                # Try to find county from text
                location = None
                for county in SWEDISH_COUNTIES:
                    if county.replace(' län', '') in text or county in text:
                        location = county
                        break
                
                results['outages'].append({
                    'incident_id': inc_id,
                    'operator': 'Telenor',
                    'source': 'telenor_web',
                    'status': 'active',
                    'description': text[:500],
                    'location': location or 'Sverige',
                    'title': f"Telenor disruption {inc_id}"
                })
        
        # Also try the specific mobile network page
        mob_response = requests.get(
            'https://www.telenor.se/support/driftinformation/driftstorningar-pa-mobilnatet/',
            headers=headers,
            timeout=15
        )
        mob_soup = BeautifulSoup(mob_response.text, 'html.parser')
        
        # Look for h2/h3 headings indicating regions
        headings = mob_soup.find_all(['h2', 'h3', 'h4', 'p'])
        for heading in headings:
            text = heading.get_text(strip=True)
            if any(c.replace(' län', '') in text for c in SWEDISH_COUNTIES) and len(text) > 5:
                location = None
                for county in SWEDISH_COUNTIES:
                    if county.replace(' län', '') in text or county in text:
                        location = county
                        break
                
                # Get surrounding content
                parent = heading.parent
                full_text = parent.get_text(strip=True) if parent else text
                
                inc_id = f"TNR{datetime.now().strftime('%Y%m%d')}{incident_count:03d}"
                incident_count += 1
                
                # Avoid duplicates
                existing_ids = {o['incident_id'] for o in results['outages']}
                if location:
                    # Check if we already have this county
                    existing_locations = {o.get('location') for o in results['outages']}
                    if location not in existing_locations:
                        results['outages'].append({
                            'incident_id': inc_id,
                            'operator': 'Telenor',
                            'source': 'telenor_mobile',
                            'status': 'active',
                            'description': full_text[:200],
                            'location': location,
                            'title': f"Telenor {location}"
                        })
        
        results['success'] = True
        logger.info(f"Telenor: found {len(results['outages'])} incidents")
        
    except Exception as e:
        logger.error(f"Telenor scrape error: {e}")
        results['error'] = str(e)
    
    return results


def scrape_tre_current() -> Dict:
    """Scrape current Tre (3) disruptions."""
    import requests
    from bs4 import BeautifulSoup
    import json as json_lib
    
    logger.info("Scraping Tre current disruptions...")
    
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'sv-SE,sv;q=0.9',
    }
    
    try:
        response = requests.get(
            'https://www.tre.se/varfor-tre/tackning/driftstorningar',
            headers=headers,
            timeout=15
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract __NEXT_DATA__
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            data = json_lib.loads(next_data.string)
            # Navigate the Next.js page props to find outage info
            page_props = data.get('props', {}).get('pageProps', {})
            
            incident_count = 0
            # Try various keys
            for key in ['outages', 'disturbances', 'faults', 'incidents', 'content', 'items']:
                if key in page_props:
                    items = page_props[key]
                    if isinstance(items, list):
                        for item in items:
                            location = None
                            for county in SWEDISH_COUNTIES:
                                if isinstance(item, dict):
                                    for v in item.values():
                                        if isinstance(v, str) and (county in v or county.replace(' län', '') in v):
                                            location = county
                                            break
                            
                            inc_id = f"TRE{datetime.now().strftime('%Y%m%d')}{incident_count:03d}"
                            incident_count += 1
                            
                            results['outages'].append({
                                'incident_id': inc_id,
                                'operator': 'Tre',
                                'source': 'tre_nextjs',
                                'status': 'active',
                                'description': str(item)[:200] if isinstance(item, dict) else str(item)[:200],
                                'location': location or 'Sverige',
                                'title': f"Tre disruption {inc_id}"
                            })
        
        # Fallback: look for county mentions in page text
        if not results['outages']:
            incident_count = 0
            paragraphs = soup.find_all(['p', 'li', 'div'])
            for para in paragraphs:
                text = para.get_text(strip=True)
                for county in SWEDISH_COUNTIES:
                    if (county in text or county.replace(' län', '') in text) and len(text) > 10:
                        inc_id = f"TRE{datetime.now().strftime('%Y%m%d')}{incident_count:03d}"
                        incident_count += 1
                        
                        existing_locations = {o.get('location') for o in results['outages']}
                        if county not in existing_locations:
                            results['outages'].append({
                                'incident_id': inc_id,
                                'operator': 'Tre',
                                'source': 'tre_html',
                                'status': 'active',
                                'description': text[:200],
                                'location': county,
                                'title': f"Tre {county}"
                            })
                        break
        
        results['success'] = True
        logger.info(f"Tre: found {len(results['outages'])} incidents")
        
    except Exception as e:
        logger.error(f"Tre scrape error: {e}")
        results['error'] = str(e)
    
    return results


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    all_results = {
        'telia': [],
        'telenor': [],
        'tre': []
    }
    
    # 1. Scrape Telia historical (2025-01-01 to now)
    logger.info("=" * 60)
    logger.info("TELIA HISTORICAL SCRAPER (2025-2026)")
    logger.info("=" * 60)
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime.now()
    
    telia_result = scrape_telia_history(start_date, end_date)
    all_results['telia'] = telia_result.get('outages', [])
    logger.info(f"Telia: {len(all_results['telia'])} incidents")
    
    # 2. Scrape Telenor current
    logger.info("\n" + "=" * 60)
    logger.info("TELENOR CURRENT SCRAPER")
    logger.info("=" * 60)
    
    telenor_result = scrape_telenor_current()
    all_results['telenor'] = telenor_result.get('outages', [])
    logger.info(f"Telenor: {len(all_results['telenor'])} incidents")
    
    # 3. Scrape Tre current
    logger.info("\n" + "=" * 60)
    logger.info("TRE CURRENT SCRAPER")
    logger.info("=" * 60)
    
    tre_result = scrape_tre_current()
    all_results['tre'] = tre_result.get('outages', [])
    logger.info(f"Tre: {len(all_results['tre'])} incidents")
    
    # Save to JSON
    output_file = 'historical_scrape_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    total = sum(len(v) for v in all_results.values())
    logger.info(f"\n✓ Saved {total} total incidents to {output_file}")
    logger.info(f"  Telia: {len(all_results['telia'])}")
    logger.info(f"  Telenor: {len(all_results['telenor'])}")
    logger.info(f"  Tre: {len(all_results['tre'])}")
