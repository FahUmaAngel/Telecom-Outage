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


from bs4 import BeautifulSoup

def extract_incidents_from_source(page_source: str, location: Optional[str] = None) -> List[Dict]:
    """Extract all incident information from page source using BeautifulSoup."""
    incidents = []
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        # Typical Telia row has at least 4 cells: ID, Description, Start, End
        # If the first cell contains INCSE, it's an incident row
        if len(cells) >= 4:
            id_cell = cells[0].get_text(strip=True)
            if 'INCSE' in id_cell:
                # Extract clean INCSE ID
                inc_id_match = re.search(r'INCSE\d+', id_cell)
                if not inc_id_match: continue
                inc_id = inc_id_match.group(0)
                
                # Description
                desc_cell = cells[1].get_text(strip=True)
                # Remove "Beskrivning" label if present
                desc = desc_cell.replace('Beskrivning', '').strip()
                
                # Dates
                start_cell = cells[2].get_text(strip=True).replace('Starttid', '').strip()
                end_cell = cells[3].get_text(strip=True).replace('Sluttid', '').strip()
                
                incident = {
                    'incident_id': inc_id,
                    'operator': 'Telia',
                    'source': 'coverage_portal',
                    'status': 'active',
                    'description': desc,
                    'location': location or 'Sverige',
                    'start_time': start_cell,
                    'estimated_end': end_cell
                }
                
                # Determine title from ID and first bit of description
                # e.g., "Telia Incident INCSE123: Just nu..."
                if desc:
                    # Clean up common generic desc: "Just nu har vi en driftstörning..."
                    short_desc = desc[:60] + "..." if len(desc) > 60 else desc
                    incident['title'] = f"{inc_id}: {short_desc}"
                else:
                    incident['title'] = f"Incident {inc_id}"
                
                incidents.append(incident)
    
    # Fallback to regex if BS finds nothing (rare, but good for safety)
    if not incidents:
        incident_ids = re.findall(r'INCSE\d+', page_source)
        for inc_id in list(set(incident_ids)):
            incidents.append({
                'incident_id': inc_id,
                'operator': 'Telia',
                'location': location or 'Sverige',
                'source': 'coverage_portal_regex',
                'status': 'active',
                'title': f"Incident {inc_id}"
            })
            
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
                    # Extract region name from parent or button text before clicking
                    try:
                        # Often the region name is next to the button or in the row above
                        region_name = button.text.replace('Visa område', '').strip()
                        if not region_name:
                            # Try to find a header or row text that might contain the region
                            row = button.find_element(By.XPATH, "./ancestor::tr")
                            region_name = row.text.replace('Visa', '').strip()
                    except:
                        region_name = None
                        
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    button.click()
                    time.sleep(4)  # Wait for content to load
                    
                    # Extract new incidents
                    new_source = driver.page_source
                    new_incidents = extract_incidents_from_source(new_source, location=region_name)
                    
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
