"""
Telia Scraper using Selenium to handle JavaScript-rendered content.
This scraper can extract actual outage data that is loaded dynamically.
"""
import json
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not installed. Install with: pip install selenium")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"


def scrape_with_selenium() -> Dict:
    """
    Scrape Telia outages using Selenium to handle JavaScript rendering.
    """
    if not SELENIUM_AVAILABLE:
        return {
            'outages': [],
            'error': 'Selenium not available',
            'success': False
        }
    
    logger.info("="*60)
    logger.info("Telia Outage Scraper (Selenium)")
    logger.info("="*60)
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    results = {
        'outages': [],
        'regions': [],
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    try:
        logger.info("Starting Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        logger.info(f"Loading page: {COVERAGE_PORTAL_URL}")
        driver.get(COVERAGE_PORTAL_URL)
        
        # Wait for page to load with explicit wait
        logger.info("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        time.sleep(8)  # Increased wait time for JavaScript to fully load
        
        # Click on "Fel" (Faults) radio button to show all outages
        try:
            logger.info("Looking for 'Fel' radio button...")
            # Try to find and click the Fel radio button
            fel_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Fel')]")
            for elem in fel_elements:
                try:
                    elem.click()
                    logger.info("✓ Clicked 'Fel' radio button")
                    time.sleep(2)
                    break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not click 'Fel' button: {e}")
        
        # Look for outage list
        logger.info("Searching for outage data...")
        
        # Try to find region list
        try:
            # Look for elements containing region names
            regions = driver.find_elements(By.XPATH, "//*[contains(text(), 'län') or contains(text(), 'Visa område')]")
            logger.info(f"Found {len(regions)} potential region elements")
            
            for region in regions:
                text = region.text.strip()
                if text and 'län' in text.lower():
                    results['regions'].append({
                        'name': text,
                        'html': region.get_attribute('outerHTML')[:200]
                    })
        except Exception as e:
            logger.warning(f"Error finding regions: {e}")
        
        # Try to extract outage tickets
        try:
            # Look for incident IDs (format: INCSE followed by numbers)
            page_source = driver.page_source
            import re
            
            # Try multiple patterns for incident IDs
            patterns = [
                r'INCSE\d+',  # Standard format
                r'INC[A-Z]{2}\d+',  # Alternative format
                r'incident["\']?\s*:\s*["\']?(INC[A-Z]{2}\d+)',  # In JSON/attributes
            ]
            
            incident_ids = set()
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                incident_ids.update(matches)
            
            incident_ids = list(incident_ids)
            logger.info(f"Found {len(incident_ids)} incident IDs: {incident_ids}")
            
            # Also check visible text elements
            try:
                text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'INC')]")
                logger.info(f"Found {len(text_elements)} elements containing 'INC'")
                for elem in text_elements[:5]:  # Check first 5
                    text = elem.text.strip()
                    if text:
                        logger.info(f"  Element text: {text[:100]}")
            except:
                pass
            
            for inc_id in incident_ids:
                results['outages'].append({
                    'incident_id': inc_id,
                    'operator': 'Telia',
                    'source': 'coverage_portal'
                })
        except Exception as e:
            logger.warning(f"Error extracting incident IDs: {e}")
        
        # Try to click on regions to get more details
        try:
            logger.info("Attempting to expand region details...")
            
            # Scroll down to make sure elements are visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            show_area_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Visa område')]")
            
            if show_area_buttons:
                logger.info(f"Found {len(show_area_buttons)} 'Visa område' buttons")
                # Try to click first few buttons to get more data
                for i, button in enumerate(show_area_buttons[:3]):  # Try first 3
                    try:
                        logger.info(f"Clicking button {i+1}...")
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        button.click()
                        time.sleep(3)  # Wait for details to load
                        
                        # Check for new incident IDs after expansion
                        new_source = driver.page_source
                        new_incidents = re.findall(r'INCSE\d+', new_source)
                        logger.info(f"  Found {len(set(new_incidents))} incidents after expansion")
                    except Exception as e:
                        logger.warning(f"  Could not click button {i+1}: {e}")
                        continue
                
                # Now try to extract detailed outage information
                page_source = driver.page_source
                
                # Save the expanded page for analysis
                with open('telia_expanded_page.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info("✓ Saved expanded page to telia_expanded_page.html")
                
                # Look for incident details
                # Pattern: INCSE followed by numbers, dates, times
                import re
                
                # Find all text that looks like incident details
                incident_pattern = r'(INCSE\d+).*?(\d{4}-\d{2}-\d{2}|\w+,\s+\w+\s+\d+,\s+\d{2}:\d{2})'
                matches = re.findall(incident_pattern, page_source, re.DOTALL)
                
                for match in matches:
                    inc_id, date_info = match
                    # Find if this incident already exists
                    existing = next((o for o in results['outages'] if o['incident_id'] == inc_id), None)
                    if existing:
                        existing['date_info'] = date_info
                    else:
                        results['outages'].append({
                            'incident_id': inc_id,
                            'date_info': date_info,
                            'operator': 'Telia',
                            'source': 'coverage_portal'
                        })
        except Exception as e:
            logger.warning(f"Error expanding regions: {e}")
        
        # Save page source for debugging
        with open('telia_selenium_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("✓ Saved page source to telia_selenium_page.html")
        
        # Take a screenshot
        try:
            driver.save_screenshot('telia_selenium_screenshot.png')
            logger.info("✓ Saved screenshot to telia_selenium_screenshot.png")
        except:
            pass
        
        results['success'] = len(results['outages']) > 0 or len(results['regions']) > 0
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        results['error'] = str(e)
    
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")
    
    logger.info("\n" + "="*60)
    logger.info(f"Scraping completed: {'SUCCESS' if results['success'] else 'FAILED'}")
    logger.info(f"Outages found: {len(results['outages'])}")
    logger.info(f"Regions found: {len(results['regions'])}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    results = scrape_with_selenium()
    
    # Save results
    output_file = "telia_selenium_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    
    # Display results
    if results['outages']:
        logger.info("\n📊 Outages found:")
        for outage in results['outages']:
            logger.info(f"  - {outage}")
    
    if results['regions']:
        logger.info("\n📍 Regions with issues:")
        for region in results['regions']:
            logger.info(f"  - {region['name']}")
