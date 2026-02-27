"""
Telia Selenium Historical Scraper (Robust Version)
Automates the Telia portal's 'Nätverkshistorik' feature with better event handling and diagnostics.
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Re-use extraction logic from telia_selenium_v3
from scrapers.telia_selenium_v3 import extract_incidents_from_source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

class TeliaHistoricalSeleniumScraper:
    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def select_network_status_tab(self):
        """Ensures the 'Nätverksstatus' tab is selected."""
        logger.info("Selecting Nätverksstatus tab...")
        try:
            # Try multiple common XPATH patterns for tabs
            xpath_patterns = [
                "//button[contains(., 'Nätverksstatus')]",
                "//div[contains(@class, 'tab') and contains(., 'Nätverksstatus')]",
                "//li[contains(., 'Nätverksstatus')]",
                "//*[contains(text(), 'Nätverksstatus')]"
            ]
            
            for pattern in xpath_patterns:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for elem in elements:
                    if elem.is_displayed():
                        logger.info(f"  Found visible element with pattern: {pattern}")
                        try:
                            elem.click()
                            time.sleep(3)
                            # Verify if we switched (usually search box changes or 'Nätverkshistorik' appears)
                            if "historik" in self.driver.page_source.lower():
                                logger.info("✓ Successfully switched to Nätverksstatus tab")
                                return True
                        except:
                            self.driver.execute_script("arguments[0].click();", elem)
                            time.sleep(3)
                            if "historik" in self.driver.page_source.lower():
                                logger.info("✓ Successfully switched to Nätverksstatus tab (via JS)")
                                return True

            # If failed, log what we DO see
            logger.warning("Could not find Nätverksstatus tab. Logging available text elements...")
            all_text = self.driver.execute_script("return document.body.innerText;")
            logger.info(f"Page text snippet: {all_text[:500]}...")
            return False
        except Exception as e:
            logger.error(f"Failed to select Nätverksstatus tab: {e}")
            return False

    def select_history_mode(self):
        """Clicks the 'Nätverkshistorik' radio button."""
        if not self.select_network_status_tab():
            return False
            
        logger.info("Enabling Nätverkshistorik...")
        try:
            # The radio button might be an input or label
            # Based on the screenshot, we definitely need to be on the right tab first.
            history_toggle = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Nätverkshistorik')] | //input[@id='searchmodehistorical']")))
            
            # Use JS click if standard click fails
            try:
                history_toggle.click()
            except:
                self.driver.execute_script("arguments[0].click();", history_toggle)
                
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Failed to enable history mode: {e}")
            return False

    def set_date_robustly(self, target_date: datetime):
        """Types the date and tries to force a blur/enter event."""
        date_str = target_date.strftime("%Y-%m-%d")
        logger.info(f"Setting date to: {date_str}")
        try:
            # Wait for any potential overlays to disappear
            time.sleep(1)
            
            # Find the date input - it might be inside a specific container for history
            # Use multiple CSS selectors
            selectors = [
                "input.date-picker-input",
                "input[placeholder='Välj datum']",
                ".search-mode-historical-container input",
                "input[type='text'][readonly]" # Sometimes they use readonly to force calendar, but we can remove it
            ]
            
            date_input = None
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            date_input = elem
                            break
                    if date_input: break
                except: continue
            
            if not date_input:
                logger.error("Could not find visible date input field")
                return False
                
            # Use JS to set value and trigger change event
            logger.info("  Setting date value via JS")
            self.driver.execute_script("""
                var input = arguments[0];
                var val = arguments[1];
                input.value = val;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
            """, date_input, date_str)
            
            time.sleep(5) # Wait for results
            return True
        except Exception as e:
            logger.error(f"Failed to set date robustly: {e}")
            return False

    def scrape_single_date(self, target_date: datetime) -> List[Dict]:
        """Scrapes all incidents for a specific date."""
        if not self.set_date_robustly(target_date):
            return []
        
        # Extract
        source = self.driver.page_source
        incidents = extract_incidents_from_source(source)
        
        # If no incidents but regions exist, try expanding one
        if not incidents:
            if "Visa område" in source:
                logger.info("  Found 'Visa område' buttons. Attempting to expand first region...")
                try:
                    btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Visa område')]")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    btn.click()
                    time.sleep(5)
                    incidents = extract_incidents_from_source(self.driver.page_source)
                except Exception as e:
                    logger.warning(f"  Failed to expand region: {e}")
        
        logger.info(f"  Result: {len(incidents)} incidents for {target_date.date()}")
        return incidents

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = TeliaHistoricalSeleniumScraper(headless=True)
    try:
        scraper.driver.get(COVERAGE_PORTAL_URL)
        time.sleep(10)
        
        if scraper.select_history_mode():
            # Test with a single recent date first to verify it works
            test_date = datetime(2026, 2, 1)
            logger.info(f"--- Verification Test: {test_date.date()} ---")
            test_results = scraper.scrape_single_date(test_date)
            
            if not test_results:
                logger.warning("Verification test found 0 incidents. Trying one more date (Feb 15)...")
                test_results = scraper.scrape_single_date(datetime(2026, 2, 15))

            # Full run
            start = datetime(2025, 1, 1)
            end = datetime(2026, 2, 27)
            
            all_historical = []
            curr = start
            while curr <= end:
                day_incidents = scraper.scrape_single_date(curr)
                for inc in day_incidents:
                    inc['captured_at'] = curr.isoformat()
                    if not any(x['incident_id'] == inc['incident_id'] for x in all_historical):
                        all_historical.append(inc)
                
                curr += timedelta(days=7)
                
            with open("telia_historical_selenium_2025_2026_robust.json", "w", encoding='utf-8') as f:
                json.dump(all_historical, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Finished. Total unique incidents: {len(all_historical)}")
            
    finally:
        scraper.close()
