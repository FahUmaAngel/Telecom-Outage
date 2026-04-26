import sys
import os
from datetime import datetime, timedelta
import logging
import time

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.historical_scraper import get_chrome_driver, extract_incidents_from_source, SWEDISH_COUNTIES, COVERAGE_PORTAL_URL
from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.engine import classify_services, classify_status, parse_swedish_date, extract_region_from_text
from scrapers.common.geocoding import get_county_coordinates

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TeliaGapRecovery")

def navigate_to_date_robust(driver, target_date_str):
    """Robust date navigation using JS injection."""
    logger.info(f"Navigating to {target_date_str} via JS...")
    try:
        # Switch to History Mode
        hist_xpath = "//div[@aria-label='Nätverkshistorik'] | //label[contains(text(), 'Nätverkshistorik')]"
        elems = driver.find_elements(By.XPATH, hist_xpath)
        if not elems:
            return False
        driver.execute_script("arguments[0].click();", elems[0])
        time.sleep(2)
        
        # Set Date via JS
        date_input = driver.find_element(By.XPATH, "//input[@placeholder='Välj datum']")
        js_script = f"""
            var el = arguments[0];
            var dateStr = '{target_date_str}';
            el.value = dateStr;
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            if (window.jQuery) {{ window.jQuery(el).trigger('change'); }}
        """
        driver.execute_script(js_script, date_input)
        
        # Trigger search (press Enter)
        date_input.send_keys(Keys.ENTER)
        time.sleep(5)
        return True
    except Exception as e:
        logger.warning(f"Robust navigation failed: {e}")
        return False

def get_area_btn(driver, short_name):
    xpaths = [
        f"//td[contains(text(), '{short_name}')]/..//span[contains(text(), 'Visa område')]",
        f"//td[contains(text(), '{short_name}')]/..//a[contains(text(), 'Visa område')]",
        f"//*[contains(text(), '{short_name}')]/..//*[contains(text(), 'Visa område')]"
    ]
    for xpath in xpaths:
        try:
            return driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            continue
    return None

def process_county(driver, county, target_date_str, all_incidents):
    logger.info(f"Processing {county}...")
    driver.get(COVERAGE_PORTAL_URL)
    time.sleep(7)
    
    if not navigate_to_date_robust(driver, target_date_str):
        return
    
    short_name = county.replace(' län', '').strip()
    area_btn = get_area_btn(driver, short_name)
        
    if area_btn:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", area_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", area_btn)
        time.sleep(6) # Wait for incident table
        
        page_source = driver.page_source
        area_incs = extract_incidents_from_source(page_source, location=county)
        
        added_count = 0
        for inc in area_incs:
            if inc['incident_id'] not in [x['incident_id'] for x in all_incidents]:
                all_incidents.append(inc)
                added_count += 1
        
        if added_count > 0:
            logger.info(f"  ✓ {county}: Found {added_count} new incidents")
        else:
            logger.info(f"  - {county}: No incidents")
    else:
        logger.info(f"  ! {county}: Area link not found")

def save_incident(db, inc, target_date_str):
    try:
        inc_id = inc['incident_id']
        location_text = inc.get('location', 'Sverige')
        desc_sv = inc.get('description', '')
        
        context_text = f"{inc_id} {location_text} {desc_sv}"
        
        normalized = NormalizedOutage(
            operator=OperatorEnum.TELIA,
            incident_id=inc_id,
            title={"sv": inc_id, "en": inc_id},
            description={"sv": desc_sv, "en": ""},
            location=location_text,
            status=OutageStatus.RESOLVED,
            severity=SeverityLevel.MEDIUM,
            affected_services=classify_services(context_text),
            source_url=COVERAGE_PORTAL_URL,
            started_at=parse_swedish_date(inc.get('start_time')),
            estimated_fix_time=parse_swedish_date(inc.get('estimated_end'))
        )
        
        county_name = extract_region_from_text(location_text, SWEDISH_COUNTIES)
        if county_name:
            normalized.location = county_name
            coords = get_county_coordinates(county_name, jitter=True)
            if coords:
                normalized.latitude, normalized.longitude = coords
        
        save_outage(db, normalized, {"source": "telia_recovery_final", "raw": inc, "recovery_date": target_date_str})
        return True
    except Exception as save_err:
        logger.error(f"Error saving {inc.get('incident_id')}: {save_err}")
        return False

def recover_telia_for_date(db, driver, wait, target_date_obj):
    target_date_str = target_date_obj.strftime("%Y-%m-%d")
    logger.info(f"--- Final Robust Recovery for Telia: {target_date_str} ---")
    
    all_incidents = []
    
    # Process each county by reloading to ensure clean state
    for county in SWEDISH_COUNTIES:
        try:
            process_county(driver, county, target_date_str, all_incidents)
        except Exception as e:
            logger.error(f"Error on {county}: {e}")
            continue

    # Save to DB
    saved_count = 0
    for inc in all_incidents:
        if save_incident(db, inc, target_date_str):
            saved_count += 1
            
    db.commit()
    logger.info(f"✓ FINISHED {target_date_str}: Total {saved_count} saved.")
    return saved_count

def run_recovery():
    db = SessionLocal()
    driver = None
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 20)
        
        start_date = datetime(2026, 4, 18)
        end_date = datetime(2026, 4, 21)
        
        current = start_date
        total_saved = 0
        while current <= end_date:
            count = recover_telia_for_date(db, driver, wait, current)
            total_saved += count
            logger.info(f"Saved {count} incidents for {current.date()}")
            current += timedelta(days=1)
            
        logger.info(f"Recovery complete. Total Telia incidents saved: {total_saved}")
        
    except Exception as e:
        logger.error(f"Fatal recovery error: {e}")
    finally:
        if driver:
            driver.quit()
        db.close()

if __name__ == "__main__":
    run_recovery()
