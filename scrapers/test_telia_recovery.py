import sys
import os
from datetime import datetime
import logging
import time

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.historical_scraper import get_chrome_driver, extract_incidents_from_source, COVERAGE_PORTAL_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TeliaTest")

def test_recovery():
    driver = None
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 30)
        
        target_date = "2026-04-18"
        logger.info(f"Testing recovery for {target_date}...")
        
        driver.get(COVERAGE_PORTAL_URL)
        logger.info("Page loaded")
        time.sleep(5)
        
        # Take initial screenshot
        driver.save_screenshot("telia_test_initial.png")
        
        # Click History
        hist_xpath = "//div[@aria-label='Nätverkshistorik'] | //label[contains(text(), 'Nätverkshistorik')]"
        logger.info(f"Looking for history button with XPath: {hist_xpath}")
        hist_btn = wait.until(EC.element_to_be_clickable((By.XPATH, hist_xpath)))
        hist_btn.click()
        logger.info("Clicked history mode")
        time.sleep(3)
        driver.save_screenshot("telia_test_history_mode.png")
        
        # Set Date
        date_xpath = "//input[@placeholder='Välj datum']"
        logger.info(f"Looking for date input: {date_xpath}")
        date_input = wait.until(EC.presence_of_element_located((By.XPATH, date_xpath)))
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys("\n")
        logger.info(f"Set date to {target_date}")
        time.sleep(5)
        driver.save_screenshot("telia_test_date_set.png")
        
        # Check if any incidents visible on main page
        page_source = driver.page_source
        incidents = extract_incidents_from_source(page_source)
        logger.info(f"Found {len(incidents)} incidents on main page")
        
        # Try one county: Stockholm
        county = "Stockholms län"
        area_xpath = "//td[contains(text(), 'Stockholm')]/..//span[contains(text(), 'Visa område')]"
        logger.info(f"Looking for area link for {county} with XPath: {area_xpath}")
        try:
            area_btn = wait.until(EC.element_to_be_clickable((By.XPATH, area_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", area_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", area_btn)
            logger.info(f"Clicked area link for {county}")
            time.sleep(5)
            driver.save_screenshot("telia_test_stockholm_expanded.png")
            
            area_source = driver.page_source
            area_incs = extract_incidents_from_source(area_source, location=county)
            logger.info(f"Found {len(area_incs)} incidents in {county}")
            for inc in area_incs:
                logger.info(f"  - {inc['incident_id']}: {inc.get('description', '')[:50]}")
        except Exception as e:
            logger.error(f"Failed to expand {county}: {e}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_recovery()
