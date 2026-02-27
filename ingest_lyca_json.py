import json
import sqlite3
import os
import sys

# Move to the project root to import common modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel, ServiceType
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status, parse_swedish_date
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES

def ingest_lyca():
    with open('lyca_selenium_results.json', 'r', encoding='utf-8') as f:
        lyca_result = json.load(f)
        
    db = SessionLocal()
    try:
        print(f"Ingesting {len(lyca_result['outages'])} Lycamobile outages...")
        for outage in lyca_result['outages']:
            location_text = outage.get('location', '')
            desc_text = outage.get('description', '')
            title_text = outage.get('title', f"Incident {outage['incident_id']}")
            context_text = f"{location_text} {desc_text} {title_text}"
            
            normalized = NormalizedOutage(
                operator=OperatorEnum.LYCAMOBILE,
                incident_id=outage['incident_id'],
                title={"sv": title_text, "en": title_text},
                description={
                    "sv": desc_text or f"Incident ID: {outage['incident_id']}",
                    "en": desc_text or f"Incident ID: {outage['incident_id']}"
                },
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
                coords = get_county_coordinates(county_name)
                if coords:
                    normalized.latitude, normalized.longitude = coords
            
            save_outage(db, normalized, {"source": "lyca_selenium_manual_ingest", "raw": outage})
            
        db.commit()
        print("Ingestion complete.")
    finally:
        db.close()

if __name__ == '__main__':
    ingest_lyca()
