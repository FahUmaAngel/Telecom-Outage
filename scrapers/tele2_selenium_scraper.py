"""
Tele2 Sweden Selenium Scraper
Scrapes mobile network outage data from https://www.tele2.se/driftstorning-mobilnatet
Uses Selenium because the page renders content dynamically via JavaScript.
"""
import json
import logging
import time
import hashlib
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"


def make_tele2_id(location: str, start_time: str) -> str:
    """Generate a clean, unique, deterministic ID for a Tele2 incident."""
    raw = f"tele2_{location}_{start_time}"
    hash_str = hashlib.sha256(raw.encode()).hexdigest()[:6].upper()
    return f"TELE2-{hash_str}"


def parse_tele2_date(date_str: str) -> Optional[datetime]:
    """Parse Swedish date strings from Tele2 page."""
    if not date_str:
        return None
    try:
        # Formats to try:
        # "2026-03-18 15:00"
        # "18 mars 2026 15:00"
        # "18/03/2026 15:00"
        
        # ISO-like
        m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', date_str)
        if m:
            return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M")
        
        # Swedish month names
        swedish_months = {
            'januari': '01', 'februari': '02', 'mars': '03', 'april': '04',
            'maj': '05', 'juni': '06', 'juli': '07', 'augusti': '08',
            'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
        }
        for sv_month, num in swedish_months.items():
            if sv_month in date_str.lower():
                clean = date_str.lower().replace(sv_month, num).strip()
                m = re.search(r'(\d{1,2})\s+(\d{2})\s+(\d{4})\s+(\d{2}:\d{2})', clean)
                if m:
                    day, month, year, time_ = m.groups()
                    return datetime.strptime(f"{year}-{month}-{day.zfill(2)} {time_}", "%Y-%m-%d %H:%M")
        
        # slash format
        m = re.search(r'(\d{2})/(\d{2})/(\d{4})\s+(\d{2}:\d{2})', date_str)
        if m:
            d, mo, y, t = m.groups()
            return datetime.strptime(f"{y}-{mo}-{d} {t}", "%Y-%m-%d %H:%M")
            
    except Exception:
        pass
    return None


def scrape_tele2_with_selenium() -> Dict:
    """Scrape Tele2 outages using Selenium (Browser automation)."""
    if not SELENIUM_AVAILABLE:
        return {'outages': [], 'error': 'Selenium not available', 'success': False}
    
    logger.info("=" * 60)
    logger.info("Tele2 Selenium Scraper")
    logger.info("=" * 60)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=sv-SE')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    driver = None
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': 'selenium_tele2'
    }
    
    try:
        logger.info("Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        
        logger.info(f"Loading: {TELE2_URL}")
        driver.get(TELE2_URL)
        time.sleep(8)  # Allow Dynamic JS to render
        
        logger.info("Page loaded. Searching for outage content...")
        
        # First, dump full page source text for analysis
        page_source = driver.page_source
        
        # Strategy 1: Look for any table/list with outage data
        outages_found = []
        
        # Try multiple selectors common to telecom outage pages
        selectors_to_try = [
            # Tables
            ("css", "table"),
            ("css", "table tr"),
            # Accordion/cards
            ("css", ".accordion"),
            ("css", ".card"),
            ("css", ".outage"),
            ("css", ".disturbance"),
            ("css", "[class*='outage']"),
            ("css", "[class*='disturbance']"),
            ("css", "[class*='driftstorning']"),
            # Generic list items
            ("css", ".status-item"),
            ("css", ".incident"),
        ]
        
        found_elements = []
        for by, selector in selectors_to_try:
            try:
                elements = driver.find_elements(
                    By.CSS_SELECTOR if by == "css" else By.XPATH, 
                    selector
                )
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    found_elements.extend([(selector, el) for el in elements])
            except:
                pass
        
        # Strategy 2: Extract all visible text content and look for outage patterns
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            all_text = body.text
            logger.info(f"Page body text length: {len(all_text)}")
            
            # Look for patterns: area names + dates
            # Tele2 often shows outages as "Ort: X, Datum: Y-Y"
            # Scan for lines with "driftstörning", "planerat", dates, county names
            lines = all_text.split('\n')
            current_group = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_group.get('location') and (current_group.get('start') or current_group.get('end')):
                        outages_found.append(dict(current_group))
                        current_group = {}
                    continue
                    
                # Date lines
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                
                # If the line has a known Swedish county
                from scrapers.common.translation import SWEDISH_COUNTIES, CITY_TO_COUNTY
                for county in SWEDISH_COUNTIES:
                    if county.lower() in line.lower():
                        current_group['location'] = county
                        break
                for city in CITY_TO_COUNTY:
                    if city.lower() in line.lower():
                        if 'location' not in current_group:
                            current_group['location'] = CITY_TO_COUNTY[city]
                        break
                
                if 'startar' in line.lower() and date_match:
                    current_group['start'] = line
                elif 'klart' in line.lower() and date_match:
                    current_group['end'] = line
                elif 'beskrivning' in line.lower():
                    current_group['description'] = line
                elif date_match and not current_group.get('start'):
                    current_group['raw_date'] = line
                    
            # Add last group if any
            if current_group.get('location'):
                outages_found.append(dict(current_group))
                
        except Exception as e:
            logger.error(f"Error extracting body text: {e}")
        
        # Strategy 3: Check for __NEXT_DATA__ like Tre
        try:
            next_data_script = driver.find_element(By.ID, '__NEXT_DATA__')
            if next_data_script:
                data = json.loads(next_data_script.get_attribute('innerHTML'))
                logger.info("Found __NEXT_DATA__ on Tele2 page!")
                # Save raw data for further analysis
                results['raw_next_data'] = str(data)[:500]
        except:
            pass
        
        # Strategy 4: Check for any JSON API calls visible in Network
        # Look for script tags that might contain outage data
        scripts = driver.find_elements(By.TAG_NAME, 'script')
        for script in scripts:
            try:
                content = script.get_attribute('innerHTML')
                if content and ('driftstörning' in content.lower() or 'outage' in content.lower()):
                    logger.info(f"Found relevant script content: {content[:200]}")
            except:
                pass
        
        # Normalize found outages
        for raw_outage in outages_found:
            location = raw_outage.get('location', '')
            if not location:
                continue
            
            start_str = raw_outage.get('start', raw_outage.get('raw_date', ''))
            end_str = raw_outage.get('end', '')
            desc = raw_outage.get('description', f'Driftstörning i {location}')
            
            start_dt = parse_tele2_date(start_str)
            end_dt = parse_tele2_date(end_str)
            
            inc_id = make_tele2_id(location, start_str or datetime.utcnow().isoformat())
            
            outage_dict = {
                'incident_id': inc_id,
                'location': location,
                'description': desc,
                'start_time': start_dt.isoformat() if start_dt else None,
                'end_time': end_dt.isoformat() if end_dt else None,
                'source_url': TELE2_URL
            }
            results['outages'].append(outage_dict)
        
        # Log page source summary for diagnosis
        logger.info(f"\nPage source snippet (first 2000 chars):\n{page_source[:2000]}")
        logger.info(f"\nTotal outages found: {len(results['outages'])}")
        results['success'] = True
        results['page_source_sample'] = page_source[:3000]
        
    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info=True)
        results['error'] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return results


if __name__ == '__main__':
    import json as json_lib
    result = scrape_tele2_with_selenium()
    print(f"\nSuccess: {result['success']}")
    print(f"Outages found: {len(result.get('outages', []))}")
    if result.get('outages'):
        for o in result['outages']:
            print(f"  - {o}")
    print("\n--- Page source sample ---")
    print(result.get('page_source_sample', 'n/a')[:1000])
