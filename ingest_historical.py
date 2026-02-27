"""
Ingest historical scrape results into the database.
Reads from historical_scrape_results.json and saves to outages table.
"""
import json
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.engine import extract_region_from_text, parse_swedish_date
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.db.connection import get_db
from scrapers.db.crud import save_outage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IngestHistorical")


OPERATOR_MAP = {
    'Telia': OperatorEnum.TELIA,
    'Telenor': OperatorEnum.TELENOR,
    'Lycamobile': OperatorEnum.LYCAMOBILE,
    'Tre': OperatorEnum.TRE,
}


def ingest_results(results_file: str):
    """Ingest results from JSON file into the database."""
    if not os.path.exists(results_file):
        logger.error(f"Results file not found: {results_file}")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        all_results = json.load(f)
    
    total_new = 0
    total_updated = 0
    
    db = next(get_db())
    
    try:
        for operator_name, outages in all_results.items():
            if not outages:
                logger.info(f"{operator_name}: No outages to ingest")
                continue
            
            logger.info(f"\nIngesting {len(outages)} outages for {operator_name}...")
            operator_enum = OPERATOR_MAP.get(operator_name.capitalize(), OperatorEnum.TELIA)
            
            for outage in outages:
                try:
                    location_text = outage.get('location', '')
                    desc_text = outage.get('description', '')
                    title_text = outage.get('title', f"Incident {outage.get('incident_id', 'UNKNOWN')}")
                    incident_id = outage.get('incident_id', f"{operator_name.upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}")
                    
                    # Determine county
                    county_name = extract_region_from_text(
                        f"{location_text} {desc_text}",
                        SWEDISH_COUNTIES
                    )
                    final_location = county_name or location_text or 'Unknown'
                    
                    # Get coordinates
                    coords = None
                    if county_name:
                        coords = get_county_coordinates(county_name, jitter=True)
                    
                    # Determine status
                    raw_status = outage.get('status', 'active')
                    status = OutageStatus.RESOLVED if raw_status == 'resolved' else OutageStatus.ACTIVE
                    
                    # Parse dates
                    start_time = parse_swedish_date(outage.get('start_time'))
                    end_time = parse_swedish_date(outage.get('estimated_end'))
                    
                    normalized = NormalizedOutage(
                        operator=operator_enum,
                        incident_id=incident_id,
                        title={"sv": title_text, "en": title_text},
                        description={"sv": desc_text or '', "en": desc_text or ''},
                        location=final_location,
                        status=status,
                        severity=SeverityLevel.MEDIUM,
                        affected_services=['mobile'],
                        source_url=outage.get('source', ''),
                        started_at=start_time,
                        estimated_fix_time=end_time,
                        latitude=coords[0] if coords else None,
                        longitude=coords[1] if coords else None,
                    )
                    
                    raw_data = {
                        'source': outage.get('source', 'historical_scraper'),
                        'raw': outage
                    }
                    
                    save_outage(db, normalized, raw_data)
                    total_new += 1
                    
                except Exception as e:
                    logger.warning(f"Error ingesting {outage.get('incident_id', 'UNKNOWN')}: {e}")
        
        db.commit()
        logger.info(f"\n✓ Ingestion complete!")
        logger.info(f"  Processed: {total_new} records")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    results_file = "historical_scrape_results.json"
    ingest_results(results_file)
