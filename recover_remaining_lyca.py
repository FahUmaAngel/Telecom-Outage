import sqlite3
import json
import time
from datetime import datetime, timedelta
import re

# Import the Selenium scraper
from scrapers.lyca_selenium_scraper import scrape_lyca_with_selenium
from scrapers.common.engine import parse_swedish_date
from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status

def recover_missing_lyca_details():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Identify the 121 missing IDs
    query = """
        SELECT incident_id 
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'lycamobile') 
        AND end_time IS NULL 
        AND estimated_fix_time IS NULL
    """
    cur.execute(query)
    missing_ids = [row[0] for row in cur.fetchall()]
    conn.close()
    
    if not missing_ids:
        print("No Lycamobile incidents found missing both end_time and estimated_fix_time.")
        return

    print(f"Targeting recovery for {len(missing_ids)} Lycamobile incidents...")
    
    # Run the improved scraper to get fresh data for ALL active incidents
    # (The portal only shows current ones, but we hope to catch the 121 if they are still active or similar)
    lyca_result = scrape_lyca_with_selenium()
    
    if not lyca_result['success']:
        print("Scraper failed to run.")
        return
        
    db = SessionLocal()
    recovered_count = 0
    
    for outage in lyca_result['outages']:
        iid = outage.get('incident_id')
        if iid in missing_ids:
            # We found one of our missing ones with full details!
            location_text = outage.get('location', '')
            desc_text = outage.get('description', '')
            title_text = outage.get('title', f"Incident {iid}")
            context_text = f"{location_text} {desc_text} {title_text}"
            
            normalized = NormalizedOutage(
                operator=OperatorEnum.LYCAMOBILE,
                incident_id=iid,
                title={"sv": title_text, "en": title_text},
                description={"sv": desc_text or f"Incident ID: {iid}", "en": desc_text or f"Incident ID: {iid}"},
                location=location_text or 'Unknown',
                status=classify_status(context_text, OutageStatus.ACTIVE),
                severity=SeverityLevel.MEDIUM,
                affected_services=classify_services(context_text),
                source_url="https://mboss.telenor.se/coverageportal?appmode=outage",
                started_at=parse_swedish_date(outage.get('start_time')),
                estimated_fix_time=parse_swedish_date(outage.get('estimated_end'))
            )
            
            county_name = extract_region_from_text(location_text, SWEDISH_COUNTIES)
            if county_name:
                normalized.location = county_name
                coords = get_county_coordinates(county_name, jitter=True)
                if coords:
                    normalized.latitude, normalized.longitude = coords
            
            # Save/Update
            save_outage(db, normalized, {"source": "lyca_recovery_fresh", "raw": outage})
            recovered_count += 1
            print(f"  Recovered details for incident {iid}")
            
    db.commit()
    db.close()
    print(f"Done. Successfully recovered details for {recovered_count} incidents.")

if __name__ == "__main__":
    recover_missing_lyca_details()
