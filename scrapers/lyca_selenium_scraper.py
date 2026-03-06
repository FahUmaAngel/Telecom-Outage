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
            # Use specific XPath that checks all inner text for the target string
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
        
        # 2. Find all county rows and save their names to process decoupled
        try:
            logger.info("Looking for county rows to expand...")
            time.sleep(2)
            
            # Fetch the names of all counties currently experiencing disturbances
            county_rows = driver.find_elements(By.XPATH, "//tr[contains(., 'län')]")
            county_names = []
            for r in county_rows:
                try:
                    name = r.text.strip().split('\n')[0].replace('Visa', '').strip()
                    if name: county_names.append(name)
                except: pass
                
            num_counties = len(county_names)
            if num_counties == 0:
                logger.warning("No counties detected.")
            else:
                logger.info(f"Found {num_counties} counties. Processing via absolute isolated unrolling...")
                
            for i, county_text in enumerate(county_names):
                try:
                    logger.info(f"Processing county {i+1}/{num_counties}: {county_text}")
                    # Hard reset state for absolute reliability on SAP SPA
                    driver.get(LYCA_BASE_URL)
                    time.sleep(6) # Wait for map
                    
                    # Re-open accordion
                    accordion = None
                    for selector in ["//button[contains(., 'I följande län')]", "//*[@id='headingOne']/button"]:
                        try:
                            accordion = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector)))
                            if accordion: break
                        except: continue
                        
                    if accordion:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
                        driver.execute_script("arguments[0].click();", accordion)
                        time.sleep(2)
                    
                    # Target specific county row
                    # Use a more robust selector for the row containing the county name
                    target_row = None
                    try:
                        target_row = wait.until(EC.presence_of_element_located((By.XPATH, f"//tr[contains(., '{county_text}')]")))
                    except:
                        logger.warning(f"  Could not find {county_text} row after reset")
                        continue
                        
                    if not target_row:
                        continue
                        
                    # Find the search/zoom icon within this row
                    zoom_icon = target_row.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
                    
                    # Scroll and click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", zoom_icon)
                    time.sleep(2) # Stabilize after scroll
                    driver.execute_script("arguments[0].click();", zoom_icon)
                    
                    logger.info(f"  Wait for incidents to load for {county_text}...")
                    # Increase wait and look for the dynamic table
                    time.sleep(8) 
                    
                    # Fetch incident rows dynamically rendered below the clicked row or in a specific results area
                    # Usually, Enghouse portals render the list in a specific div or table
                    incident_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    found_for_county = 0
                    
                    logger.info(f"  Found {len(incident_rows)} total rows in DOM after click")
                    
                    for ir in incident_rows:
                        cells = ir.find_elements(By.TAG_NAME, "td")
                        
                        # Incidents typically have 5 cols
                        if len(cells) >= 4:
                            incident_id = None
                            desc_idx = 2
                            start_idx = 3
                            end_idx = 4
                            
                            # Validate 8-digit Telenor IDs
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
                                    'operator': 'Lycamobile',
                                    'location': county_text,
                                    'description': description,
                                    'start_time': started_at,
                                    'estimated_end': est_end,
                                    'status': 'active'
                                }
                                
                                short_desc = description[:60] + "..." if len(description) > 60 else description
                                incident['title'] = f"{county_text}: {short_desc}" if description else f"Lycamobile Incident {incident_id} ({county_text})"
                                
                                # Prevent duplicates
                                existing_ids = {o['incident_id'] for o in results['outages']}
                                if incident_id not in existing_ids:
                                    results['outages'].append(incident)
                                    found_for_county += 1
                                    logger.info(f"  + Added incident {incident_id} in {county_text}")
                                    
                    if found_for_county == 0:
                        logger.info(f"  No new incidents found in DOM for {county_text}")
                        
                except Exception as e:
                    logger.warning(f"  Error processing county {county_text}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error iterating counties: {e}")
            
        # 4. Fallback: Parse whole page for incident IDs ONLY IF table logic failed completely
        if not results['outages']:
            logger.info("Table extraction failed, falling back to regex extraction...")
            page_text = driver.page_source
            ids = set(re.findall(r'\b\d{8}\b', page_text))
            for id_str in ids:
                results['outages'].append({
                    'incident_id': id_str,
                    'operator': 'Lycamobile',
                    'location': 'Sverige',
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
