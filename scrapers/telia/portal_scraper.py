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
from typing import List, Dict, Optional, Tuple
from playwright.sync_api import sync_playwright

from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import CITY_TO_COUNTY, SWEDISH_COUNTIES
from scrapers.common.engine import extract_region_from_text, parse_swedish_date, classify_status
from scrapers.common.models import OutageStatus

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


def interact_with_portal(page):
    """Triggers UI interactions to load incidents."""
    try:
        fel_btn = page.locator("text=Fel").first
        if fel_btn.is_visible():
            fel_btn.click()
            page.wait_for_timeout(3000)
    except Exception: pass

    visa_links = page.locator("text=Visa område")
    count = visa_links.count()
    for i in range(min(count, 10)):
        try:
            link = visa_links.nth(i)
            link.scroll_into_view_if_needed(timeout=2000)
            link.click(timeout=2000)
            page.wait_for_timeout(2000)
            f_btn = page.locator("text=Fel").first
            if f_btn.is_visible(): f_btn.click()
        except Exception: pass


def handle_portal_response(response, captured, token_container):
    """Handles responses from the Telia portal."""
    if "coverageportal" not in response.url:
        return
        
    ert_match = re.search(r'ert=([^&]+)', response.url)
    if ert_match and not token_container[0]:
        token_container[0] = urllib.parse.unquote(ert_match.group(1))
        logger.info("Captured ERT token")

    if response.status == 200 and "AreaTicketList" in response.url:
        try:
            data = response.json()
            if isinstance(data, list) and data:
                logger.info(f"Intercepted {len(data)} incidents")
                captured.extend(data)
        except Exception as e:
            logger.debug(f"JSON err: {e}")

def run_playwright_capture() -> Tuple[List[Dict], Optional[str]]:
    """Runs Playwright session to capture incidents and session token."""
    captured = []
    token = [None]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        page.on("response", lambda r: handle_portal_response(r, captured, token))

        try:
            page.goto(f"{BASE_URL}?appmode=outage", wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(2000)
            interact_with_portal(page)
            if not captured: page.wait_for_timeout(10000)
        except Exception as e:
            logger.error(f"PW err: {e}")
        finally:
            browser.close()

    return captured, token[0]


def extract_incident_coords(item, county_name):
    """Extracts or resolves coordinates for an incident."""
    bbox = item.get("BBox", {})
    ll = bbox.get("LL", {})
    lat = ll.get("Northing") or item.get("Northing")
    lon = ll.get("Easting") or item.get("Easting")

    if not lat or not lon:
        county_geo = f"{county_name} län" if county_name and 'län' not in county_name.lower() else county_name
        coords = get_county_coordinates(county_geo, jitter=True)
        lat, lon = coords if coords else (58.0, 14.0)
    return lat, lon

def parse_incident_dates(item):
    """Cleans and parses start/end times."""
    def clean(val):
        if not val: return None
        if isinstance(val, str) and "/Date(" in val:
            m = re.search(r'\d+', val)
            if m: return datetime.fromtimestamp(int(m.group()) / 1000).isoformat() + "+01:00"
        return parse_swedish_date(val) if isinstance(val, str) and len(val) > 5 else None

    start = clean(item.get("StartTimeStr") or item.get("EventTime"))
    end = clean(item.get("EstimatedEndTimeStr") or item.get("EstimatedCloseTime"))
    return start, end

def process_single_incident(item, telia_id, region_id_map, timestamp, cursor):
    """Processes and saves a single incident to the DB."""
    inc_id = item.get("ExternalId")
    if not inc_id: return

    county_name = item.get("CountyName") or ""
    if county_name.lower() == "unknown": county_name = ""
    
    # Use pre-resolved coordinates and city
    lat = item.get('_resolved_lat')
    lon = item.get('_resolved_lon')
    precise_city = item.get('_resolved_city')
    
    raw_location = ", ".join([p for p in [precise_city, item.get("AreaName"), county_name] if p])
    location = extract_region_from_text(raw_location, SWEDISH_COUNTIES) or (county_name if county_name else (item.get("AreaName") or "Unknown"))
    region_id = region_id_map.get(location)

    start_time, end_time = parse_incident_dates(item)
    desc_raw = item.get("Description") or item.get("Text") or ""
    
    status = classify_status(desc_raw)
    if status == OutageStatus.SCHEDULED:
        logger.info(f"Skipping scheduled incident: {inc_id}")
        return
        
    services = json.dumps(extract_services(desc_raw + " " + item.get("AffectedServices", "")))
    
    title_json = json.dumps({"sv": str(inc_id), "en": str(inc_id)})
    desc_json = json.dumps({"sv": desc_raw, "en": desc_raw})

    cursor.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (inc_id, telia_id))
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE outages SET location=?, region_id=?, latitude=?, longitude=?, start_time=?, end_time=NULL, estimated_fix_time=NULL,
            description=?, affected_services=?, title=?, updated_at=?, status=? WHERE id=?
        """, (location, region_id, lat, lon, start_time, desc_json, services, title_json, timestamp, status.value, row[0]))
    else:
        cursor.execute("""
            INSERT INTO outages (incident_id, operator_id, region_id, title, description, location, latitude, longitude,
            start_time, end_time, estimated_fix_time, status, severity, affected_services, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'medium', ?, ?, ?)
        """, (inc_id, telia_id, region_id, title_json, desc_json, location, lat, lon, start_time, status.value, services, timestamp, timestamp))


def scrape_portal_granular():
    """Main function with enhanced per-incident location resolution."""
    logger.info("Starting Enhanced Telia Portal Scraper...")

    captured, token = run_playwright_capture()
    if not captured:
        logger.error("No incidents captured")
        return

    # Deduplicate
    unique_incidents = {item.get("ExternalId"): item for item in captured if item.get("ExternalId")}
    logger.info(f"Processing {len(unique_incidents)} unique incidents. Token: {'Yes' if token else 'No'}")

    # Resolve locations BEFORE opening the database transaction to prevent locking
    logger.info("Resolving locations for incidents...")
    for inc_id, item in unique_incidents.items():
        county_name = item.get("CountyName") or ""
        if county_name.lower() == "unknown": county_name = ""
        lat, lon = extract_incident_coords(item, county_name)
        
        precise_city = None
        if lat and lon:
            # We only sleep and request if we actually need to resolve
            precise_city = resolve_location_name(lat, lon)
            
        item['_resolved_lat'] = lat
        item['_resolved_lon'] = lon
        item['_resolved_city'] = precise_city

    db_path = get_db_path()
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM operators WHERE name = 'telia'")
        res = cursor.fetchone()
        if not res:
            logger.error("Telia operator not found")
            return
        telia_id = res[0]

        cursor.execute("SELECT id, name FROM regions")
        region_id_map = {}
        for rid, name_json in cursor.fetchall():
            try:
                sv_name = json.loads(name_json).get('sv')
                region_id_map[sv_name] = rid
            except Exception:
                region_id_map[name_json] = rid

        timestamp = datetime.now().isoformat()
        for item in unique_incidents.values():
            process_single_incident(item, telia_id, region_id_map, timestamp, cursor)
        
        conn.commit()
    logger.info("Scraping complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_portal_granular()
