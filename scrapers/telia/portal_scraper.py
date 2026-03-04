"""
Granular Telia Portal Scraper (Synchronous Playwright)
Extracts town-level locations, detailed status, and 2G/4G/5G services.
"""
import logging
import re
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple
from playwright.sync_api import sync_playwright

from scrapers.common.geocoding import get_county_coordinates

logger = logging.getLogger("TeliaPortalScraper")

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
    return list(set(services))

def get_db_path() -> str:
    # Database is usually in the root
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'telecom_outage.db')

def sync_to_db(incidents: Dict):
    if not incidents: return 0, 0
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get Telia ID
    cursor.execute("SELECT id FROM operators WHERE name = 'telia'")
    result = cursor.fetchone()
    if not result:
        logger.error("Telia operator not found in database")
        conn.close()
        return 0, 0
    telia_id = result[0]
    
    timestamp = datetime.now().isoformat()
    ins, upd = 0, 0
    
    for inc_id, data in incidents.items():
        coords = get_county_coordinates(data['county'], jitter=True)
        lat, lon = coords if coords else (58.0, 14.0)
        
        title_json = json.dumps({"sv": f"{inc_id}: {data['nature']}", "en": f"{inc_id}: {data['nature']}"})
        desc_json = json.dumps({"sv": data['description'], "en": data['description']})
        services_json = json.dumps(data['services'])
        
        cursor.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (inc_id, telia_id))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE outages SET location = ?, latitude = ?, longitude = ?, start_time = ?, estimated_fix_time = ?, 
                                 description = ?, affected_services = ?, title = ?, updated_at = ?, status = 'ACTIVE'
                WHERE id = ?
            """, (data['location'], lat, lon, data['start'], data['end'], desc_json, services_json, title_json, timestamp, row[0]))
            upd += 1
        else:
            cursor.execute("""
                INSERT INTO outages (incident_id, operator_id, title, description, location, latitude, longitude, 
                                   start_time, estimated_fix_time, status, severity, affected_services, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 'MEDIUM', ?, ?, ?)
            """, (inc_id, telia_id, title_json, desc_json, data['location'], lat, lon, data['start'], data['end'], services_json, timestamp, timestamp))
            ins += 1
            
    conn.commit()
    conn.close()
    return ins, upd

def scrape_portal_granular():
    """Main function to run the portal scraper by intercepting the internal Ticket API response."""
    logger.info("Starting Intercepting Telia Portal Scraper (Interactive)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a realistic user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        captured_data = []

        # Intercept the API response
        def handle_response(response):
            # The URL might have query parameters, so we check if it contains the endpoint
            if "AreaTicketList" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"Intercepted API response with {len(data)} incidents from {response.url[:100]}...")
                        captured_data.extend(data)
                except Exception as e:
                    logger.warning(f"Failed to parse intercepted response: {e}")

        page.on("response", handle_response)
        
        try:
            url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
            logger.info(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle", timeout=90000)
            
            # 1. Click "Fel" (Faults)
            fel_btn = page.locator("text=Fel").first
            if fel_btn.is_visible():
                logger.info("Clicking 'Fel' button...")
                fel_btn.click()
                page.wait_for_timeout(3000)
            
            # 2. To trigger API calls, we might need to click some regions or "Visa område"
            # Find a few "Visa område" links and click them
            visa_links = page.locator("text=Visa område")
            count = visa_links.count()
            logger.info(f"Found {count} 'Visa område' links to interact with.")
            
            # Interact with the first 5 regions to trigger multiple API calls (various areas)
            for i in range(min(count, 5)):
                try:
                    link = visa_links.nth(i)
                    logger.info(f"Interacting with region {i+1}...")
                    link.scroll_into_view_if_needed()
                    link.click()
                    page.wait_for_timeout(3000)
                    # Click "Fel" again to go back or keep it open
                    if fel_btn.is_visible(): fel_btn.click()
                except Exception as e:
                    logger.warning(f"Error during interaction {i}: {e}")

            if not captured_data:
                logger.info("Still no data. Trying one final wait...")
                page.wait_for_timeout(10000)

            if not captured_data:
                logger.error("No incident data intercepted. The portal might be using a different API or blocking Playwright.")
                return

            # Deduplicate by ExternalId
            unique_incidents = {}
            for item in captured_data:
                inc_id = item.get("ExternalId")
                if inc_id and inc_id not in unique_incidents:
                    unique_incidents[inc_id] = item

            logger.info(f"Processing {len(unique_incidents)} unique incidents")
            
            incidents_to_sync = {}
            for inc_id, item in unique_incidents.items():
                # Extract coordinates from BBox
                bbox = item.get("BBox", {})
                ll = bbox.get("LL", {})
                lat = ll.get("Northing") or item.get("Northing")
                lon = ll.get("Easting") or item.get("Easting")
                
                # Metadata
                desc_raw = item.get("Description") or item.get("Text") or ""
                location_name = item.get("AreaName") or "Unknown"
                county = item.get("CountyName") or "Unknown"
                
                # Parse dates
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
                
                services_txt = item.get("AffectedServices", "")
                services = extract_services(desc_raw + " " + services_txt)
                
                incidents_to_sync[inc_id] = {
                    "location": f"{location_name}, {county}",
                    "county": f"{county} län" if county != "Unknown" and 'län' not in county.lower() else county,
                    "description": desc_raw,
                    "latitude": lat,
                    "longitude": lon,
                    "start": start_time or datetime.now().isoformat(),
                    "end": end_time,
                    "services": services,
                    "nature": item.get("FaultType") or "ACTIVE"
                }

            if incidents_to_sync:
                db_path = get_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM operators WHERE name = 'telia'")
                res = cursor.fetchone()
                if not res:
                    logger.error("Telia operator not found")
                    conn.close()
                    return
                telia_id = res[0]
                
                timestamp = datetime.now().isoformat()
                ins, upd = 0, 0
                
                for inc_id, data in incidents_to_sync.items():
                    lat, lon = data['latitude'], data['longitude']
                    if not lat or not lon:
                        coords = get_county_coordinates(data['county'], jitter=True)
                        lat, lon = coords if coords else (58.0, 14.0)
                    
                    title_json = json.dumps({"sv": f"{inc_id}: {data['nature']}", "en": f"{inc_id}: {data['nature']}"})
                    desc_json = json.dumps({"sv": data['description'], "en": data['description']})
                    services_json = json.dumps(data['services'])
                    
                    cursor.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (inc_id, telia_id))
                    row = cursor.fetchone()
                    
                    if row:
                        cursor.execute("""
                            UPDATE outages SET location = ?, latitude = ?, longitude = ?, start_time = ?, estimated_fix_time = ?, 
                                             description = ?, affected_services = ?, title = ?, updated_at = ?, status = 'ACTIVE'
                            WHERE id = ?
                        """, (data['location'], lat, lon, data['start'], data['end'], desc_json, services_json, title_json, timestamp, row[0]))
                        upd += 1
                    else:
                        cursor.execute("""
                            INSERT INTO outages (incident_id, operator_id, title, description, location, latitude, longitude, 
                                               start_time, estimated_fix_time, status, severity, affected_services, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 'MEDIUM', ?, ?, ?)
                        """, (inc_id, telia_id, title_json, desc_json, data['location'], lat, lon, data['start'], data['end'], services_json, timestamp, timestamp))
                        ins += 1
                
                conn.commit()
                conn.close()
                logger.info(f"Sync completed. Total: {ins} Created, {upd} Updated.")
            else:
                logger.warning("No incidents processed.")

        except Exception as e:
            logger.error(f"Fatal error in portal scraper: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_portal_granular()
