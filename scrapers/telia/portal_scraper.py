"""
Enhanced Telia Portal Scraper with per-incident location resolution.
Uses the intercepted Outage/GetLocationInfo endpoint to resolve precise municipality names.
"""
import logging
import re
import os
import json
import sqlite3
import requests
import time
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright

from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import CITY_TO_COUNTY, SWEDISH_COUNTIES

logger = logging.getLogger("TeliaPortalScraper")

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
SERVICES_PARAM = "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE"


def parse_swedish_date(date_str: str) -> str:
    """Parses Swedish relative dates like 'fre 27.feb 10:39' into ISO format."""
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'maj': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
    }
    date_str = str(date_str).lower()
    m = re.search(r'(\d{1,2})\.([a-zåäö]+)\s+(\d{2}:\d{2})', date_str)
    if m:
        day = int(m.group(1))
        month_str = m.group(2)
        time_str = m.group(3)
        month = months.get(month_str[:3], 1)
        now = datetime.now()
        year = now.year
        if month > now.month + 1: year -= 1
        return f"{year}-{month:02d}-{day:02d}T{time_str}:00+01:00"
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+01:00")


def extract_services(text: str) -> List[str]:
    """Strictly filters for 2G, 4G, and 5G services."""
    services = []
    t = text.lower()
    if '5g' in t: services.append("5g")
    if '4g' in t or 'lte' in t: services.append("4g")
    if '2g' in t or 'gsm' in t: services.append("2g")
    return list(set(services)) or ["4g"]


def get_db_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'telecom_outage.db')


def resolve_location_name(lat: float, lon: float) -> Optional[str]:
    """
    Reverse geocode using OpenStreetMap Nominatim API to get municipality/city name.
    Respects Nominatim's 1-request-per-second usage policy.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
        headers = {'User-Agent': 'TelecomOutageMonitor/1.0 (Telia Scraper Component)'}
        
        # Sleep to respect rate limits
        time.sleep(1.2)
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get('address', {})
            
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality')
            if city:
                if ' kommun' in city:
                    city = city.replace(' kommun', '')
                return city
    except Exception as e:
        logger.debug(f"Error in Nominatim resolve_location_name: {e}")
    return None


def scrape_portal_granular():
    """Main function with enhanced per-incident location resolution."""
    logger.info("Starting Enhanced Telia Portal Scraper...")

    captured_incidents = []
    session_token = [None]
    fault_cache_keys_ref = [""]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            if "coverageportal" not in response.url:
                return
            
            # Capture ERT token from any successful URL
            ert_match = re.search(r'ert=([^&]+)', response.url)
            if ert_match and not session_token[0]:
                session_token[0] = urllib.parse.unquote(ert_match.group(1))
                logger.info(f"Captured ERT token from response URL")

            if response.status != 200:
                return

            try:
                if "AreaTicketList" in response.url and response.status == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Intercepted AreaTicketList with {len(data)} incidents")
                        captured_incidents.extend(data)
                
                # Capture fault cache keys for later use
                if "FaultsLastUpdatedInfo" in response.url:
                    data = response.json()
                    ck = data.get("ActiveCacheKey", "")
                    pk = data.get("PlannedCacheKey", "")
                    if ck:
                        fault_cache_keys_ref[0] = f"PW,{pk},16|AF,{ck},2"
                        logger.info(f"Captured fault cache keys")
            except Exception as e:
                logger.debug(f"Error handling response: {e}")

        page.on("response", handle_response)

        try:
            url = f"{BASE_URL}?appmode=outage"
            logger.info(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(2000)

            # Click Fel to start the flow (triggers API calls)
            try:
                fel_btn = page.locator("text=Fel").first
                if fel_btn.is_visible():
                    fel_btn.click()
                    page.wait_for_timeout(3000)
            except:
                pass

            # Interact with region links to trigger AreaTicketList calls
            visa_links = page.locator("text=Visa område")
            count = visa_links.count()
            logger.info(f"Found {count} 'Visa område' links")

            for i in range(min(count, 10)):
                try:
                    link = visa_links.nth(i)
                    link.scroll_into_view_if_needed(timeout=2000)
                    link.click(timeout=2000)
                    page.wait_for_timeout(2000)
                    try:
                        fel_btn = page.locator("text=Fel").first
                        if fel_btn.is_visible():
                            fel_btn.click()
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"Error on region {i}: {e}")

            if not captured_incidents:
                page.wait_for_timeout(10000)

        except Exception as e:
            logger.error(f"Fatal error in portal scraper: {e}")
        finally:
            browser.close()

    if not captured_incidents:
        logger.error("No incidents captured from portal")
        return

    logger.info(f"Processing {len(captured_incidents)} captured incidents")

    # Set up a requests session with the captured ERT token
    http_session = requests.Session()
    http_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": BASE_URL,
        "Accept": "application/json",
    })

    token = session_token[0]
    fault_cache_keys = fault_cache_keys_ref[0]
    logger.info(f"Token available: {'Yes' if token else 'No'}")

    # Deduplicate by ExternalId
    unique_incidents = {}
    for item in captured_incidents:
        inc_id = item.get("ExternalId")
        if inc_id and inc_id not in unique_incidents:
            unique_incidents[inc_id] = item

    logger.info(f"Processing {len(unique_incidents)} unique incidents")

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM operators WHERE name = 'telia'")
    res = cursor.fetchone()
    if not res:
        logger.error("Telia operator not found in DB")
        conn.close()
        return
    telia_id = res[0]

    timestamp = datetime.now().isoformat()
    ins, upd = 0, 0

    for inc_id, item in unique_incidents.items():
        # --- Get coordinates ---
        bbox = item.get("BBox", {})
        ll = bbox.get("LL", {})
        lat = ll.get("Northing") or item.get("Northing")
        lon = ll.get("Easting") or item.get("Easting")

        # --- Resolve precise location name via Nominatim ---
        precise_city = None
        if lat and lon:
            precise_city = resolve_location_name(lat, lon)

        # --- Build location string ---
        area_name = item.get("AreaName") or "Unknown"
        county_name = item.get("CountyName") or ""
        
        # Don't use "Unknown" as a county name
        if county_name.lower() == "unknown":
            county_name = ""
            
        if precise_city:
            location = f"{precise_city}, {county_name}" if county_name else precise_city
            logger.info(f"  {inc_id}: Resolved to '{location}' via Nominatim")
        else:
            location = f"{area_name}, {county_name}" if county_name else area_name

        # --- County for geocoding ---
        county_for_geo = f"{county_name} län" if county_name and 'län' not in county_name.lower() else county_name
        if not lat or not lon:
            coords = get_county_coordinates(county_for_geo, jitter=True)
            lat, lon = coords if coords else (58.0, 14.0)

        # --- Parse dates ---
        def clean_date(val):
            if not val: return None
            if isinstance(val, str) and "/Date(" in val:
                m = re.search(r'\d+', val)
                if m:
                    ts = int(m.group()) / 1000
                    return datetime.fromtimestamp(ts).isoformat() + "+01:00"
            if isinstance(val, str) and len(val) > 5:
                return parse_swedish_date(val)
            return None

        start_time = clean_date(item.get("StartTimeStr") or item.get("EventTime"))
        end_time = clean_date(item.get("EstimatedEndTimeStr") or item.get("EstimatedCloseTime"))

        # --- Services ---
        desc_raw = item.get("Description") or item.get("Text") or ""
        services_txt = item.get("AffectedServices", "")
        services = extract_services(desc_raw + " " + services_txt)

        # --- Build DB record ---
        title_json = json.dumps({"sv": f"{inc_id}: {item.get('FaultType', 'ACTIVE')}", "en": f"{inc_id}: {item.get('FaultType', 'ACTIVE')}"})
        desc_json = json.dumps({"sv": desc_raw, "en": desc_raw})
        services_json = json.dumps(services)

        cursor.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (inc_id, telia_id))
        row = cursor.fetchone()

        if row:
            cursor.execute("""
                UPDATE outages 
                SET location = ?, latitude = ?, longitude = ?, start_time = ?, estimated_fix_time = ?,
                    description = ?, affected_services = ?, title = ?, updated_at = ?, status = 'active'
                WHERE id = ?
            """, (location, lat, lon, start_time, end_time, desc_json, services_json, title_json, timestamp, row[0]))
            upd += 1
        else:
            cursor.execute("""
                INSERT INTO outages 
                    (incident_id, operator_id, title, description, location, latitude, longitude,
                     start_time, estimated_fix_time, status, severity, affected_services, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 'medium', ?, ?, ?)
            """, (inc_id, telia_id, title_json, desc_json, location, lat, lon, start_time, end_time, services_json, timestamp, timestamp))
            ins += 1

    conn.commit()
    conn.close()
    logger.info(f"Done. Created: {ins}, Updated: {upd}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_portal_granular()
