import logging
import re
import os
import json
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import sys

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.engine import classify_services, parse_swedish_date, extract_region_from_text
from scrapers.common.geocoding import get_county_coordinates

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("TeliaPlaywrightRecovery")

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]

def run_recovery():
    db = SessionLocal()
    captured_incidents = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            if "AreaTicketList" in response.url or "RegionFaultList" in response.url:
                try:
                    if response.status == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Intercepted {len(data)} incidents from {response.url}")
                            captured_incidents.extend(data)
                except Exception as e:
                    logger.debug(f"Error parsing response: {e}")

        page.on("response", handle_response)

        start_date = datetime(2026, 4, 18)
        end_date = datetime(2026, 4, 21)
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            logger.info(f"--- Recovering Telia for {date_str} ---")
            
            try:
                page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
                
                # Click 'Nätverkshistorik'
                hist_btn = page.locator("//div[@aria-label='Nätverkshistorik'] | //label[contains(text(), 'Nätverkshistorik')]").first
                if hist_btn.is_visible():
                    hist_btn.click()
                    page.wait_for_timeout(2000)
                
                # Set Date
                date_input = page.locator("//input[@placeholder='Välj datum']").first
                if date_input.is_visible():
                    # Clear and type is better than JS for triggering app state sometimes
                    date_input.click()
                    # Use JS to set value to be sure
                    page.evaluate(f"el => {{ el.value = '{date_str}'; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}", date_input.element_handle())
                    page.keyboard.press("Enter")
                    
                    # Wait for data to load
                    logger.info(f"Waiting for incidents for {date_str}...")
                    page.wait_for_timeout(10000)
                    
                    # If no incidents intercepted yet, try clicking the map or some counties
                    try:
                        if not captured_incidents:
                            logger.info("No incidents intercepted yet, clicking a few counties...")
                            visa_links = page.locator("text=Visa område")
                            v_count = visa_links.count()
                            if v_count > 0:
                                for i in range(min(v_count, 3)):
                                    try:
                                        visa_links.nth(i).click(timeout=5000)
                                        page.wait_for_timeout(3000)
                                    except: pass
                    except: pass
                
                # Process captured for this day (MOVED OUTSIDE UI INTERACTION TRY)
                if captured_incidents:
                    saved = process_incidents(db, captured_incidents, date_str)
                    logger.info(f"✓ Saved {saved} unique incidents for {date_str}")
                    captured_incidents = [] # Reset for next day
                else:
                    logger.warning(f"! No incidents found for {date_str}")

            except Exception as e:
                logger.error(f"Error on {date_str}: {e}")
            
            current_date += timedelta(days=1)

        browser.close()
    db.close()

def process_incidents(db, incidents, recovery_date):
    unique_map = {}
    for item in incidents:
        inc_id = item.get("ExternalId") or item.get("incident_id")
        if inc_id:
            unique_map[inc_id] = item
    
    saved_count = 0
    timestamp = datetime.now().isoformat()
    
    for inc_id, item in unique_map.items():
        try:
            # Basic normalization
            desc_sv = item.get("Description") or item.get("Text") or ""
            area_name = item.get("AreaName") or ""
            county_name = item.get("CountyName") or ""
            
            location_text = f"{area_name}, {county_name}" if area_name and county_name else (area_name or county_name or "Sverige")
            
            # Dates
            def parse_date(val):
                if not val: return None
                if "/Date(" in str(val):
                    m = re.search(r'\d+', str(val))
                    if m: return datetime.fromtimestamp(int(m.group())/1000).isoformat() + "+01:00"
                return parse_swedish_date(val)

            start_time = parse_date(item.get("StartTimeStr") or item.get("EventTime"))
            
            normalized = NormalizedOutage(
                operator=OperatorEnum.TELIA,
                incident_id=inc_id,
                title={"sv": inc_id, "en": inc_id},
                description={"sv": desc_sv, "en": ""},
                location=location_text,
                status=OutageStatus.RESOLVED,
                severity=SeverityLevel.MEDIUM,
                affected_services=classify_services(desc_sv),
                source_url=BASE_URL,
                started_at=start_time,
                estimated_fix_time=parse_date(item.get("EstimatedEndTimeStr") or item.get("EstimatedCloseTime"))
            )
            
            # Regional Geocoding
            std_region = extract_region_from_text(location_text, SWEDISH_COUNTIES)
            if std_region:
                normalized.location = std_region
                coords = get_county_coordinates(std_region, jitter=True)
                if coords:
                    normalized.latitude, normalized.longitude = coords
            
            save_outage(db, normalized, {"source": "telia_playwright_recovery", "raw": item, "recovery_date": recovery_date})
            saved_count += 1
        except Exception as e:
            logger.error(f"Save error for {inc_id}: {e}")
            
    db.commit()
    return saved_count

if __name__ == "__main__":
    run_recovery()
