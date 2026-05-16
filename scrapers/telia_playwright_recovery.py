import logging
import re
import os
import json
import time
import argparse
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
COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]

def setup_context(browser):
    """Sets up browser context with user agent."""
    return browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

def handle_recovery_response(response, captured):
    """Intercepts AreaTicketList responses."""
    if "AreaTicketList" in response.url and response.status == 200:
        try:
            data = response.json()
            if isinstance(data, list) and data:
                logger.info(f"Intercepted {len(data)} incidents")
                captured.extend(data)
        except Exception as e:
            logger.debug(f"JSON error: {e}")

def trigger_date_navigation(page, target_date_str):
    """Triggers date navigation via JS."""
    try:
        hist_xpath = "//div[@aria-label='Nätverkshistorik'] | //label[contains(text(), 'Nätverkshistorik')]"
        page.locator(hist_xpath).first.click(timeout=5000)
        page.wait_for_timeout(2000)

        date_input = page.locator("//input[@placeholder='Välj datum']").first
        js_script = """
            (params) => {
                var el = params.el;
                var dateStr = params.dateStr;
                el.value = dateStr;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                if (window.jQuery) { window.jQuery(el).trigger('change'); }
            }
        """
        page.evaluate(
            js_script,
            {"el": date_input.element_handle(), "dateStr": target_date_str},
        )
        date_input.press("Enter")
        page.wait_for_timeout(5000)
        return True
    except Exception as e:
        logger.warning(f"Nav fail: {e}")
        return False

def run_recovery(start_date: datetime, end_date: datetime):
    db = SessionLocal()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = setup_context(browser)
            page = context.new_page()
            captured = []
            page.on("response", lambda r: handle_recovery_response(r, captured))

            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                logger.info(f"Recovering {date_str}...")
                page.goto(COVERAGE_PORTAL_URL, wait_until="networkidle")
                
                if trigger_date_navigation(page, date_str):
                    process_incidents(db, captured, date_str)
                    captured.clear()
                
                current += timedelta(days=1)
            browser.close()
    finally:
        db.close()

def map_and_save_recovery_incident(db, item, target_date_str):
    """Maps a single raw incident to NormalizedOutage and saves it."""
    inc_id = item.get("ExternalId")
    if not inc_id: return False
    
    loc_text = item.get("CountyName") or item.get("AreaName") or "Sverige"
    desc_sv = item.get("Description") or item.get("Text") or ""
    
    normalized = NormalizedOutage(
        operator=OperatorEnum.TELIA,
        incident_id=inc_id,
        title={"sv": inc_id, "en": inc_id},
        description={"sv": desc_sv, "en": ""},
        location=loc_text,
        status=OutageStatus.RESOLVED,
        severity=SeverityLevel.MEDIUM,
        affected_services=classify_services(desc_sv + " " + (item.get("AffectedServices") or "")),
        source_url=COVERAGE_PORTAL_URL,
        started_at=parse_swedish_date(item.get("StartTimeStr")),
        estimated_fix_time=parse_swedish_date(item.get("EstimatedEndTimeStr"))
    )
    
    county = extract_region_from_text(loc_text, SWEDISH_COUNTIES)
    if county:
        normalized.location = county
        coords = get_county_coordinates(county, jitter=True)
        if coords: normalized.latitude, normalized.longitude = coords
    
    save_outage(db, normalized, {"source": "telia_recovery", "raw": item, "date": target_date_str})
    return True

def process_incidents(db, items, target_date_str):
    """Batch processes a list of raw incidents."""
    unique = {it.get("ExternalId"): it for it in items if it.get("ExternalId")}
    logger.info(f"Processing {len(unique)} unique incidents for {target_date_str}")
    
    count = 0
    for item in unique.values():
        try:
            if map_and_save_recovery_incident(db, item, target_date_str):
                count += 1
        except Exception as e:
            logger.error(f"Save error for {item.get('ExternalId')}: {e}")
            
    db.commit()
    logger.info(f"Saved {count} incidents for {target_date_str}")

def parse_args():
    parser = argparse.ArgumentParser(description="Recover Telia historical incidents for a date range.")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_recovery(
        start_date=datetime.strptime(args.start_date, "%Y-%m-%d"),
        end_date=datetime.strptime(args.end_date, "%Y-%m-%d"),
    )
