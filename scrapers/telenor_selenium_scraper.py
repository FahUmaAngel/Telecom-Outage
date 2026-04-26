"""
Telenor Selenium Scraper
Handles dynamic content and county expansion to extract all outages.
"""
import json
import logging
import time
from typing import List, Dict
from datetime import datetime
import re

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELENOR_BASE_URL = "https://mboss.telenor.se/coverageportal?appmode=outage"

def expand_accordion(driver, wait):
    try:
        logger.info("Looking for disturbances accordion...")
        accordion = None
        for selector in ["//button[contains(., 'I följande län')]", "//*[@id='headingOne']/button"]:
            try:
                if selector.startswith("//") or selector.startswith("/*"):
                    accordion = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    accordion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if accordion: break
            except: continue
        
        if accordion:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
            time.sleep(1)
            is_collapsed = "collapsed" in accordion.get_attribute("class") or accordion.get_attribute("aria-expanded") == "false"
            if is_collapsed:
                logger.info("Clicking to expand accordion...")
                driver.execute_script("arguments[0].click();", accordion)
                time.sleep(3)
            else:
                logger.info("Accordion already expanded")
        else:
            logger.warning("Could not find accordion button")
    except Exception as e:
        logger.warning(f"Error handling accordion: {e}")

def get_county_names(driver) -> List[str]:
    county_names = []
    try:
        logger.info("Looking for county rows to expand...")
        time.sleep(2)
        county_rows = driver.find_elements(By.XPATH, "//tr[contains(., 'län')]")
        for r in county_rows:
            try:
                name = r.text.strip().split('\n')[0].replace('Visa', '').strip()
                if name: 
                    name = name.split('(')[0].replace('County', 'län').strip()
                    county_names.append(name)
            except: pass
    except Exception as e:
        logger.warning(f"Error getting county names: {e}")
    return county_names

def parse_incident_row(cells, county_text, results, found_for_county):
    if len(cells) < 4:
        return found_for_county
        
    incident_id = None
    desc_idx = 2
    start_idx = 3
    end_idx = 4
    
    if re.match(r'^\d{8}$', cells[0].text.strip()):
        incident_id = cells[0].text.strip()
        desc_idx, start_idx, end_idx = 1, 2, 3
    elif len(cells) >= 5 and re.match(r'^\d{8}$', cells[1].text.strip()):
        incident_id = cells[1].text.strip()
        desc_idx, start_idx, end_idx = 2, 3, 4
        
    if incident_id:
        description = cells[desc_idx].text.strip() if desc_idx < len(cells) else ""
        started_at = cells[start_idx].text.strip() if start_idx < len(cells) else ""
        est_end = cells[end_idx].text.strip() if end_idx < len(cells) else ""
        
        incident = {
            'incident_id': incident_id,
            'operator': 'Telenor',
            'location': county_text,
            'description': description,
            'start_time': started_at,
            'estimated_end': est_end,
            'status': 'active',
            'title': incident_id
        }
        
        existing_ids = {o['incident_id'] for o in results['outages']}
        if incident_id not in existing_ids:
            results['outages'].append(incident)
            found_for_county += 1
            logger.info(f"  + Added incident {incident_id} in {county_text}")
            
    return found_for_county

def process_county(driver, wait, county_text, results):
    try:
        driver.get(TELENOR_BASE_URL)
        time.sleep(6)
        
        expand_accordion(driver, wait)
        
        target_row = None
        try:
            target_row = wait.until(EC.presence_of_element_located((By.XPATH, f"//tr[contains(., '{county_text}')]")))
        except:
            logger.warning(f"  Could not find {county_text} row after reset")
            return
            
        if not target_row:
            return
            
        zoom_icon = target_row.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", zoom_icon)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", zoom_icon)
        
        logger.info(f"  Wait for incidents to load for {county_text}...")
        time.sleep(8) 
        
        incident_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        found_for_county = 0
        logger.info(f"  Found {len(incident_rows)} total rows in DOM after click")
        
        for ir in incident_rows:
            cells = ir.find_elements(By.TAG_NAME, "td")
            found_for_county = parse_incident_row(cells, county_text, results, found_for_county)
                
        if found_for_county == 0:
            logger.info(f"  No new incidents found in DOM for {county_text}")
            
    except Exception as e:
        logger.warning(f"  Error processing county {county_text}: {e}")

def extract_fallback_ids(driver, results):
    if not results['outages']:
        logger.info("Table extraction failed, falling back to regex extraction...")
        page_text = driver.page_source
        ids = set(re.findall(r'\b\d{8}\b', page_text))
        for id_str in ids:
            results['outages'].append({
                'incident_id': id_str,
                'operator': 'Telenor',
                'location': 'Sverige',
                'status': 'active'
            })

def scrape_telenor_with_selenium() -> Dict:
    """Scrape Telenor outages using Selenium."""
    if not SELENIUM_AVAILABLE:
        return {'outages': [], 'error': 'Selenium not available', 'success': False}
    
    logger.info("="*60)
    logger.info("Telenor Selenium Scraper")
    logger.info("="*60)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': 'selenium_telenor'
    }
    
    try:
        logger.info("Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        
        logger.info(f"Loading: {TELENOR_BASE_URL}")
        driver.get(TELENOR_BASE_URL)
        time.sleep(10)
        
        expand_accordion(driver, wait)
        
        county_names = get_county_names(driver)
        num_counties = len(county_names)
        
        if num_counties == 0:
            logger.warning("No counties detected.")
        else:
            logger.info(f"Found {num_counties} counties. Processing via absolute isolated unrolling...")
            for i, county_text in enumerate(county_names):
                logger.info(f"Processing county {i+1}/{num_counties}: {county_text}")
                process_county(driver, wait, county_text, results)
                
        extract_fallback_ids(driver, results)
        
        driver.save_screenshot('telenor_selenium_screenshot.png')
        with open('telenor_selenium_final.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("✓ Saved HTML and screenshot")
        
        results['success'] = len(results['outages']) > 0
        
    except Exception as e:
        logger.error(f"Critical Error: {e}", exc_info=True)
        results['error'] = str(e)
    
    finally:
        if driver:
            driver.quit()
    
    logger.info("\n" + "="*60)
    logger.info(f"Result: {'SUCCESS' if results['success'] else 'FAILED'}")
    logger.info(f"Total outages: {len(results['outages'])}")
    logger.info("="*60)
    
    return results

if __name__ == "__main__":
    res = scrape_telenor_with_selenium()
    with open('telenor_selenium_results.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"Results saved to telenor_selenium_results.json")
