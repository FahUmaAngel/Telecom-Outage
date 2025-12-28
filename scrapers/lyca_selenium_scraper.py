"""
Lycamobile (via Telenor) Selenium Scraper
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

LYCA_BASE_URL = "https://mboss.telenor.se/coverageportal?appmode=outage"

def scrape_lyca_with_selenium() -> Dict:
    """Scrape Lycamobile (Telenor) outages using Selenium."""
    if not SELENIUM_AVAILABLE:
        return {'outages': [], 'error': 'Selenium not available', 'success': False}
    
    logger.info("="*60)
    logger.info("Lycamobile/Telenor Selenium Scraper")
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
        'method': 'selenium_lyca'
    }
    
    try:
        logger.info("Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        
        logger.info(f"Loading: {LYCA_BASE_URL}")
        driver.get(LYCA_BASE_URL)
        time.sleep(10) # Wait for initial map and content
        
        # 1. Expand the "I följande län har vi för närvarande störningar" accordion
        try:
            logger.info("Looking for disturbances accordion...")
            # Try multiple selectors for the accordion
            accordion = None
            for selector in [".accordion-button", "//button[contains(text(), 'I följande län')]", "//*[@id='headingOne']/button"]:
                try:
                    if selector.startswith("//") or selector.startswith("/*"):
                        accordion = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        accordion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    if accordion: break
                except: continue
            
            if accordion:
                # Scroll to it first
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
                time.sleep(1)
                
                # Check if it's already expanded or not
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
        
        # 2. Find all county rows
        try:
            logger.info("Looking for county rows...")
            # Wait for the table to be visible after expansion
            time.sleep(2)
            
            # Find all rows that contain "län"
            rows = driver.find_elements(By.XPATH, "//tr[contains(., 'län')]")
            counties_data = []
            
            for row in rows:
                try:
                    # Look for the magnifying glass in this row
                    zoom_icon = row.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
                    county_text = row.text.strip()
                    # Extract the county name (usually the first part before any numbers/icons)
                    county_name = county_text.split('\n')[0].replace('Visa', '').strip()
                    
                    counties_data.append({
                        'name': county_name,
                        'element': zoom_icon
                    })
                    logger.info(f"Detected county: {county_name}")
                except Exception as row_e:
                    continue
            
            if not counties_data:
                logger.warning("No counties detected in the table.")
            else:
                logger.info(f"Found {len(counties_data)} counties with disturbances")
            
            # 3. Iterate through counties and extract specific incidents
            num_counties = len(counties_data)
            for i in range(num_counties):
                try:
                    # Re-find the county rows to avoid stale elements
                    rows = driver.find_elements(By.XPATH, "//tr[contains(., 'län')]")
                    if i >= len(rows): break
                    
                    row = rows[i]
                    zoom_icon = row.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
                    county_text = row.text.strip().split('\n')[0].replace('Visa', '').strip()
                    
                    logger.info(f"Processing county {i+1}/{num_counties}: {county_text}")
                    
                    # Scroll and click zoom icon
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", zoom_icon)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", zoom_icon)
                    logger.info(f"  Wait for incident table for {county_text}...")
                    time.sleep(6) # Wait for incidents table to populate
                    
                    # Extract incidents from the newly populated table "Alla aktuella störningar i området"
                    incident_table_rows = driver.find_elements(By.XPATH, "//h6[contains(text(), 'Alla aktuella störningar i området')]/following-sibling::div//table/tbody/tr")
                    
                    if not incident_table_rows:
                        # Fallback to general table search if structure is slightly different
                        incident_table_rows = driver.find_elements(By.CSS_SELECTOR, ".table-responsive table tbody tr")
                    
                    for row in incident_table_rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 4:
                            incident_id = cells[0].text.strip()
                            if re.match(r'^\d{8}$', incident_id): # Telenor IDs are 8 digits
                                description = cells[1].text.strip()
                                started_at = cells[2].text.strip()
                                est_end = cells[3].text.strip()
                                
                                incident = {
                                    'incident_id': incident_id,
                                    'operator': 'Lycamobile',
                                    'location': county['name'],
                                    'description': description,
                                    'start_time': started_at,
                                    'estimated_end': est_end,
                                    'status': 'active'
                                }
                                
                                # Prevent duplicates
                                existing_ids = {o['incident_id'] for o in results['outages']}
                                if incident_id not in existing_ids:
                                    results['outages'].append(incident)
                                    logger.info(f"  + Added incident {incident_id}")
                
                except Exception as e:
                    logger.warning(f"  Error processing county {county['name']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error iterating counties: {e}")
        
        # 4. Fallback: Parse whole page for incident IDs if table logic failed
        if not results['outages']:
            logger.info("Table extraction failed, falling back to regex extraction...")
            page_text = driver.page_source
            ids = set(re.findall(r'\b\d{8}\b', page_text))
            for id_str in ids:
                results['outages'].append({
                    'incident_id': id_str,
                    'operator': 'Lycamobile',
                    'status': 'active'
                })
        
        # Save artifacts
        driver.save_screenshot('lyca_selenium_screenshot.png')
        with open('lyca_selenium_final.html', 'w', encoding='utf-8') as f:
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
    res = scrape_lyca_with_selenium()
    with open('lyca_selenium_results.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"Results saved to lyca_selenium_results.json")
