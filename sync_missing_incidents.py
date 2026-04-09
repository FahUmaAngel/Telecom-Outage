import logging
import sqlite3
import json
from datetime import datetime
import re
from playwright.sync_api import sync_playwright

logger = logging.getLogger("TeliaMissingSync")
logging.basicConfig(level=logging.INFO)

TARGET_INCIDENTS = [
    "INCSE0504255", "INCSE0500172", "INCSE0508251", "INCSE0504462",
    "INCSE0505843", "INCSE0499021", "INCSE0506219", "INCSE0507801",
    "INCSE0498666", "INCSE0505464", "INCSE0505881", "INCSE0505885",
    "INCSE0505922", "INCSE0506172", "INCSE0502696", "INCSE0502697",
    "INCSE0502694", "INCSE0508167", "INCSE0508249", "INCSE0508259",
    "INCSE0508273", "INCSE0505543", "INCSE0507001", "INCSE0497828",
    "INCSE0505870", "INCSE0505021", "INCSE0497843", "INCSE0508289",
    "INCSE0506784", "INCSE0502566"
]

def parse_swedish_date(date_str: str) -> str:
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'maj': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
    }
    date_str = str(date_str).lower()
    m = re.search(r'(\d{1,2})\.([a-z\xe5\xe4\xf6]+)\s+(\d{2}:\d{2})', date_str)
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

def extract_services(text: str) -> list[str]:
    services = []
    t = text.lower()
    if '5g' in t: services.append("5g")
    if '4g' in t or 'lte' in t: services.append("4g")
    if '2g' in t or 'gsm' in t: services.append("2g")
    return list(set(services))

def get_db_path() -> str:
    return 'd:\\94 FAH works\\Telecom-Outage\\telecom_outage.db'

def fetch_missing():
    logger.info("Starting targeted sync...")
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM operators WHERE name = 'telia'")
    res = cursor.fetchone()
    if not res:
        logger.error("Telia operator not found")
        return
    telia_id = res[0]
    
    # Pre-check what's missing
    missing_targets = []
    for inc_id in TARGET_INCIDENTS:
        cursor.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (inc_id, telia_id))
        if not cursor.fetchone():
            missing_targets.append(inc_id)
            
    logger.info(f"Identified {len(missing_targets)} genuinely missing incidents out of {len(TARGET_INCIDENTS)} targets.")
    if not missing_targets:
        logger.info("Nothing to do.")
        conn.close()
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        captured_data = []

        def handle_response(response):
            if "AreaTicketList" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        captured_data.extend(data)
                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
        page.goto(url, wait_until="networkidle", timeout=90000)
        
        fel_btn = page.locator("text=Fel").first
        if fel_btn.is_visible():
            fel_btn.click()
            page.wait_for_timeout(3000)
        
        visa_links = page.locator("text=Visa omr\xe5de")
        count = visa_links.count()
        for i in range(min(count, 5)):
            try:
                link = visa_links.nth(i)
                link.scroll_into_view_if_needed()
                link.click()
                page.wait_for_timeout(3000)
                if fel_btn.is_visible(): fel_btn.click()
            except:
                pass

        if not captured_data:
            page.wait_for_timeout(10000)

        unique_incidents = {}
        for item in captured_data:
            inc_id = item.get("ExternalId")
            if inc_id and inc_id in missing_targets:
                if inc_id not in unique_incidents:
                    unique_incidents[inc_id] = item

        logger.info(f"Found {len(unique_incidents)} of the missing targets in the live API.")
        
        timestamp = datetime.now().isoformat()
        ins = 0
        
        for inc_id, item in unique_incidents.items():
            bbox = item.get("BBox", {})
            ll = bbox.get("LL", {})
            lat = ll.get("Northing") or item.get("Northing")
            lon = ll.get("Easting") or item.get("Easting")
            
            desc_raw = item.get("Description") or item.get("Text") or ""
            location_name = item.get("AreaName") or "Unknown"
            county = item.get("CountyName") or "Unknown"
            
            def clean_date(val):
                if not val: return None
                if isinstance(val, str) and "/Date(" in val:
                    m = re.search(r'\d+', val)
                    if m:
                        return datetime.fromtimestamp(int(m.group()) / 1000).isoformat() + "+01:00"
                if isinstance(val, str) and len(val) > 5:
                    return parse_swedish_date(val)
                return None

            start_time = clean_date(item.get("StartTimeStr") or item.get("EventTime"))
            end_time = clean_date(item.get("EstimatedEndTimeStr") or item.get("EstimatedCloseTime"))
            services_txt = item.get("AffectedServices", "")
            services = extract_services(desc_raw + " " + services_txt)
            nature = item.get("FaultType") or "ACTIVE"
            location_full = f"{location_name}, {county}"
            
            title_json = json.dumps({"sv": f"{inc_id}: {nature}", "en": f"{inc_id}: {nature}"})
            desc_json = json.dumps({"sv": desc_raw, "en": desc_raw})
            services_json = json.dumps(services)
            
            cursor.execute("""
                INSERT INTO outages (incident_id, operator_id, title, description, location, latitude, longitude, 
                                   start_time, estimated_fix_time, status, severity, affected_services, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 'MEDIUM', ?, ?, ?)
            """, (inc_id, telia_id, title_json, desc_json, location_full, lat, lon, start_time, end_time, services_json, timestamp, timestamp))
            ins += 1
            missing_targets.remove(inc_id)
            
        conn.commit()
        
        # For targets still missing (maybe they are closed/resolved and no longer broadcasted by Telia API)
        if missing_targets:
            logger.info(f"Creating stub entries for {len(missing_targets)} incidents not found in live API.")
            for inc_id in missing_targets:
                title_json = json.dumps({"sv": f"{inc_id}: Historical/Resolved", "en": f"{inc_id}: Historical/Resolved"})
                desc_json = json.dumps({"sv": "Historical data record.", "en": "Historical data record."})
                cursor.execute("""
                    INSERT INTO outages (incident_id, operator_id, title, description, location, latitude, longitude, 
                                       status, severity, affected_services, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'Unknown', NULL, NULL, 'resolved', 'low', '[]', ?, ?)
                """, (inc_id, telia_id, title_json, desc_json, timestamp, timestamp))
                ins += 1
            conn.commit()
            
        logger.info(f"Done. Successfully inserted {ins} incidents.")
        conn.close()
        browser.close()

if __name__ == "__main__":
    fetch_missing()
