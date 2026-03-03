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
    """Main function to run the portal scraper."""
    logger.info("Starting Granular Telia Portal Scraper...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Click "Fel" (Faults) button
            fel_btn = page.locator("text=Fel").first
            if fel_btn.is_visible():
                fel_btn.click()
                page.wait_for_timeout(2000)
            else:
                logger.error("Could not find 'Fel' button")
                return
            
            # Find all region links
            locs = page.locator("text=Visa område")
            count = locs.count()
            logger.info(f"Found {count} regions to process")
            
            total_ins, total_upd = 0, 0
            
            for i in range(count):
                try:
                    link = locs.nth(i)
                    # Extract region name (e.g., Stockholms län)
                    reg_name = link.evaluate("el => el.closest('tr').innerText.split('\\n')[0].trim()")
                    if 'län' not in reg_name.lower(): 
                        continue
                    
                    logger.info(f"[{i+1}/{count}] Processing {reg_name}...")
                    link.scroll_into_view_if_needed()
                    link.click()
                    page.wait_for_timeout(4000)
                    
                    # Area Town identification
                    area_town = reg_name
                    h_text = page.evaluate('''() => {
                        let h = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,div.table-title,span.table-title,p.table-title'));
                        let t = h.find(el => el.innerText.includes('Störningar i') || el.innerText.includes('Disturbances in'));
                        return t ? t.innerText : null;
                    }''')
                    if h_text:
                        clean = h_text.replace('Störningar i', '').replace('Disturbances in', '').strip()
                        if clean: area_town = f"{clean}, {reg_name}"

                    # Sidebar details (Status & Services)
                    sidebar = page.evaluate('''() => {
                        let els = Array.from(document.querySelectorAll('.active-outage-info, .outage-info-container, div, span'));
                        let status = els.find(el => el.innerText.match(/Reducerad kapacitet|Begränsad täckning|Ingen täckning/));
                        let serv = els.find(el => el.innerText.includes('Påverkade tjänster'));
                        return {
                            status: status ? status.innerText.trim() : "active",
                            servicesTxt: serv ? serv.parentElement.innerText : ""
                        };
                    }''')
                    
                    reg_incidents = {}
                    # Scrape all incident rows in the expanded region
                    rows = page.locator("tr").all()
                    for row in rows:
                        if row.locator("td[data-plot]").count() > 0:
                            tds = row.locator("td").all_inner_texts()
                            if len(tds) >= 4:
                                mid = re.search(r'INCSE\d+', tds[0])
                                if mid:
                                    inc_id = mid.group()
                                    desc_raw = tds[1].replace('Beskrivning', '').strip()
                                    services = extract_services(desc_raw + " " + sidebar['servicesTxt'])
                                    
                                    reg_incidents[inc_id] = {
                                        "location": area_town,
                                        "county": reg_name,
                                        "description": desc_raw,
                                        "start": parse_swedish_date(tds[2].replace('Starttid', '')),
                                        "end": parse_swedish_date(tds[3].replace('Sluttid', '')),
                                        "services": services,
                                        "nature": sidebar['status']
                                    }
                    
                    if reg_incidents:
                        ins, upd = sync_to_db(reg_incidents)
                        total_ins += ins
                        total_upd += upd
                        logger.info(f"  -> {area_town}: {len(reg_incidents)} tickets (Synced: {ins} New, {upd} Upd)")
                    
                    # Refresh state for next region
                    btn_fel = page.locator("text=Fel").first
                    if btn_fel.is_visible():
                        btn_fel.click()
                        page.wait_for_timeout(1500)
                        
                except Exception as e:
                    logger.error(f"Error processing region {i}: {e}")
                    # Try to recover by going back to the main fault list
                    page.goto(url)
                    page.wait_for_timeout(2000)
                    page.locator("text=Fel").first.click()
                    page.wait_for_timeout(2000)

            logger.info(f"Scrape completed. Total: {total_ins} Created, {total_upd} Updated.")

        except Exception as e:
            logger.error(f"Fatal error in portal scraper: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_portal_granular()
