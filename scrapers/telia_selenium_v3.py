"""
Improved Selenium Scraper - Version 3
Fixes stale element issues and extracts all incident data properly.
"""
import json
import logging
import time
from typing import List, Dict, Optional
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

COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"


def extract_incidents_from_source(page_source: str) -> List[Dict]:
    """Extract all incident information from page source."""
    incidents = []
    
    # Find all INCSE incident IDs
    incident_ids = re.findall(r'INCSE\d+', page_source)
    incident_ids = list(set(incident_ids))
    
    for inc_id in incident_ids:
        incident = {
            'incident_id': inc_id,
            'operator': 'Telia',
            'source': 'coverage_portal',
            'status': 'active'
        }
        
        # Try to find context around this incident
        pattern = rf'{inc_id}[^<]*(?:<[^>]+>[^<]*)*?(?:(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)[^<]*\d{{2}}:\d{{2}})'
        matches = re.findall(pattern, page_source, re.DOTALL)
        
        if matches:
            context = matches[0][:300]
            # Extract dates
            date_pattern = r'((?:Sat|Sun|Mon|Tue|Wed|Thu|Fri),?\s+\w+\s+\d+,?\s+\d{2}:\d{2})'
            dates = re.findall(date_pattern, context)
            if dates:
                incident['start_time'] = dates[0]
                if len(dates) > 1:
                    incident['estimated_end'] = dates[1]
        
        incidents.append(incident)
    
    return incidents


def scrape_with_selenium_v3() -> Dict:
    """Enhanced Selenium scraper with better extraction."""
    if not SELENIUM_AVAILABLE:
        return {'outages': [], 'error': 'Selenium not available', 'success': False}
    
    logger.info("="*60)
    logger.info("Telia Selenium Scraper V3 (Improved)")
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
        'method': 'selenium_v3'
    }
    
    try:
        logger.info("Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        logger.info(f"Loading: {COVERAGE_PORTAL_URL}")
        driver.get(COVERAGE_PORTAL_URL)
        time.sleep(8)
        
        # Click "Fel" button
        try:
            fel_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Fel')]")
            for elem in fel_elements:
                try:
                    elem.click()
                    logger.info("✓ Clicked 'Fel' button")
                    time.sleep(3)
                    break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not click 'Fel': {e}")
        
        # Extract incidents from current page
        page_source = driver.page_source
        initial_incidents = extract_incidents_from_source(page_source)
        logger.info(f"Found {len(initial_incidents)} incidents initially")
        results['outages'].extend(initial_incidents)
        
        # Try to expand regions and get more data
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Get all "Visa område" buttons
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    # Re-find buttons each time to avoid stale elements
                    buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Visa område')]")
                    
                    if attempt >= len(buttons):
                        break
                    
                    logger.info(f"Clicking region button {attempt + 1}/{min(max_attempts, len(buttons))}...")
                    
                    # Scroll to button and click
                    button = buttons[attempt]
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    button.click()
                    time.sleep(4)  # Wait for content to load
                    
                    # Extract new incidents
                    new_source = driver.page_source
                    new_incidents = extract_incidents_from_source(new_source)
                    
                    # Add only new incidents (avoid duplicates)
                    existing_ids = {o['incident_id'] for o in results['outages']}
                    for inc in new_incidents:
                        if inc['incident_id'] not in existing_ids:
                            results['outages'].append(inc)
                            existing_ids.add(inc['incident_id'])
                    
                    logger.info(f"  Total unique incidents: {len(results['outages'])}")
                    
                except StaleElementReferenceException:
                    logger.warning(f"  Stale element at button {attempt + 1}, continuing...")
                    continue
                except Exception as e:
                    logger.warning(f"  Error at button {attempt + 1}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error expanding regions: {e}")
        
        # Save final page source
        with open('telia_selenium_v3_final.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        driver.save_screenshot('telia_selenium_v3_screenshot.png')
        logger.info("✓ Saved HTML and screenshot")
        
        results['success'] = len(results['outages']) > 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
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
    results = scrape_with_selenium_v3()
    
    output_file = "telia_selenium_v3_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Saved to: {output_file}")
    
    if results['outages']:
        logger.info(f"\n📊 Found {len(results['outages'])} outages:")
        for i, outage in enumerate(results['outages'][:5], 1):
            logger.info(f"\n  {i}. {outage['incident_id']}")
            if 'start_time' in outage:
                logger.info(f"     Start: {outage.get('start_time', 'N/A')}")
            if 'estimated_end' in outage:
                logger.info(f"     End: {outage.get('estimated_end', 'N/A')}")
        
        if len(results['outages']) > 5:
            logger.info(f"\n  ... and {len(results['outages']) - 5} more")
