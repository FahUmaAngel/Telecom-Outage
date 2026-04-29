"""
Main scraper runner.
Executes all scrapers and saves to DB.
"""
import logging
from scrapers.telenor.fetch import scrape_telenor_outages
from scrapers.telenor.parser import parse_telenor_outages
from scrapers.telenor.mapper import map_telenor_outages

from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages
from scrapers.tre.mapper import map_tre_outages

from scrapers.telia import scrape_telia_outages, parse_telia_outages, scrape_portal_granular

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES, create_bilingual_text
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status, parse_swedish_date

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ScraperRunner")

def _run_telia_scraper(db):
    """Execution logic for Telia scraper."""
    try:
        logger.info("Running Telia (Enhanced API Scraper)...")
        raw_outages = scrape_telia_outages()
        parsed_outages = parse_telia_outages(raw_outages)
        
        if parsed_outages:
            logger.info(f"✓ Telia API scraper found {len(parsed_outages)} outages")
            for outage in parsed_outages:
                inc_id = outage.get('id', 'N/A')
                desc = outage.get('description', {})
                location_text = outage.get('location', 'Sweden')
                context_text = f"{inc_id} {location_text} {desc.get('sv', '')}"
                
                normalized = NormalizedOutage(
                    operator=OperatorEnum.TELIA,
                    incident_id=inc_id,
                    title={"sv": inc_id, "en": inc_id},
                    description=desc,
                    location=location_text,
                    status=classify_status(context_text, OutageStatus.ACTIVE),
                    severity=SeverityLevel.MEDIUM,
                    affected_services=outage.get('affected_services', classify_services(context_text)),
                    source_url="https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage",
                    started_at=parse_swedish_date(outage.get('start_time')),
                    estimated_fix_time=parse_swedish_date(outage.get('estimated_fix_time'))
                )
                
                county_name = extract_region_from_text(location_text, SWEDISH_COUNTIES)
                if county_name:
                    normalized.location = county_name
                    coords = get_county_coordinates(county_name, jitter=True)
                    if coords:
                        normalized.latitude, normalized.longitude = coords
                
                save_outage(db, normalized, {"source": "telia_api_enhanced", "raw": outage})
            
            db.commit()
        else:
            logger.warning("! Telia API scraper found no outages - falling back to Playwright Portal Scraper")
            scrape_portal_granular()
            logger.info("Telia Portal Scraper fallback completed")
    except Exception as e:
        logger.error(f"Telia enhanced scraper failed: {e}", exc_info=True)
        db.rollback()

def _process_telenor_outage(db, outage):
    """Helper to process and save a single Telenor outage."""
    location_text = outage.get('location', '')
    desc_text = outage.get('description', '')
    title_text = outage.get('title', f"Incident {outage['incident_id']}")
    context_text = f"{location_text} {desc_text} {title_text}"
    
    normalized = NormalizedOutage(
        operator=OperatorEnum.TELENOR,
        incident_id=outage['incident_id'],
        title={"sv": outage['incident_id'], "en": outage['incident_id']},
        description=create_bilingual_text(desc_text or f"Incident ID: {outage['incident_id']}"),
        location=location_text or 'Unknown',
        status=classify_status(context_text, OutageStatus.ACTIVE),
        severity=SeverityLevel.MEDIUM,
        affected_services=[s for s in classify_services(context_text) if s.value not in ['voice', 'data']],
        source_url="https://mboss.telenor.se/coverageportal?appmode=outage",
        started_at=parse_swedish_date(outage.get('start_time')),
        estimated_fix_time=parse_swedish_date(outage.get('estimated_end'))
    )
    
    search_text = location_text if location_text else context_text
    county_name = extract_region_from_text(search_text, SWEDISH_COUNTIES)
    if county_name:
        normalized.location = county_name
        coords = get_county_coordinates(county_name, jitter=True)
        if coords:
            normalized.latitude, normalized.longitude = coords
    
    save_outage(db, normalized, {"source": "telenor_selenium", "raw": outage})

def _run_telenor_scraper(db):
    """Execution logic for Telenor scraper."""
    try:
        logger.info("Running Telenor (Selenium)...")
        from scrapers.telenor_selenium_scraper import scrape_telenor_with_selenium
        telenor_result = scrape_telenor_with_selenium()
        
        if telenor_result['success']:
            logger.info(f"✓ Telenor scraper succeeded. Found {len(telenor_result['outages'])} outages")
            for outage in telenor_result['outages']:
                _process_telenor_outage(db, outage)
            
            db.commit()
        else:
            logger.error("✗ Telenor scraper failed")
    except Exception as e:
        logger.error(f"Telenor failed with exception: {e}", exc_info=True)
        db.rollback()

def _run_tre_scraper(db):
    """Execution logic for Tre scraper."""
    try:
        logger.info("Running Tre...")
        raw = scrape_tre_outages()
        parsed = parse_tre_outages(raw)
        mapped = map_tre_outages(parsed)
        
        for item in mapped:
            save_outage(db, item, {"source": "tre_scraper"})
            
        db.commit()
        logger.info(f"Tre: processed {len(mapped)} outages")
    except Exception as e:
        logger.error(f"Tre failed: {e}")
        db.rollback()

def run_scrapers():
    """Main entry point to run all scrapers."""
    logger.info("Starting scraper run...")
    db = SessionLocal()
    try:
        _run_telia_scraper(db)
        _run_telenor_scraper(db)
        _run_tre_scraper(db)
    finally:
        db.close()
    logger.info("Scraper run completed.")

if __name__ == "__main__":
    run_scrapers()
