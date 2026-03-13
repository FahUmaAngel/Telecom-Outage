"""
Main scraper runner.
Executes all scrapers and saves to DB.
"""
import logging
import sys
import os

# Telia scraper now uses telia_scraper.py with fallback
# from scrapers.telia.fetch_enhanced import scrape_telia_outages
# from scrapers.telia.parser_enhanced import parse_telia_outages
# from scrapers.telia.mapper_enhanced import map_telia_outages

from scrapers.lycamobile.fetch import scrape_lyca_outages
from scrapers.lycamobile.parser import parse_lyca_outages
from scrapers.lycamobile.mapper import map_lyca_outages

from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages
from scrapers.tre.mapper import map_tre_outages

from scrapers.telia import scrape_telia_outages, parse_telia_outages, scrape_portal_granular

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status, parse_swedish_date

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ScraperRunner")

def run_scrapers():
    logger.info("Starting scraper run...")
    db = SessionLocal()
    
    try:
        # 1. Telia (Enhanced API-based with regional awareness)
        try:
            logger.info("Running Telia (Enhanced API Scraper)...")
            
            # Fetch all outages (Now includes _region_name in raw_data)
            raw_outages = scrape_telia_outages()
            parsed_outages = parse_telia_outages(raw_outages)
            
            if parsed_outages:
                logger.info(f"✓ Telia API scraper found {len(parsed_outages)} outages")
                save_count = 0
                for outage in parsed_outages:
                    inc_id = outage.get('id', 'N/A')
                    desc = outage.get('description', {})
                    location_text = outage.get('location', 'Sweden')
                    
                    context_text = f"{inc_id} {location_text} {desc.get('sv', '')}"
                    
                    normalized = NormalizedOutage(
                        operator=OperatorEnum.TELIA,
                        incident_id=inc_id,
                        title={"sv": f"Incident {inc_id}", "en": f"Incident {inc_id}"},
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
                    save_count += 1
                
                db.commit()
                logger.info(f"Telia API: saved {save_count} outages")
            else:
                logger.warning("! Telia API scraper found no outages - falling back to Playwright Portal Scraper")
                scrape_portal_granular()
                logger.info("Telia Portal Scraper fallback completed")
        except Exception as e:
            logger.error(f"Telia enhanced scraper failed: {e}", exc_info=True)
            db.rollback()

        # 2. Lycamobile (Selenium)
        try:
            logger.info("Running Lycamobile (Selenium)...")
            from scrapers.lyca_selenium_scraper import scrape_lyca_with_selenium
            
            lyca_result = scrape_lyca_with_selenium()
            
            if lyca_result['success']:
                logger.info(f"✓ Lycamobile scraper succeeded")
                logger.info(f"  Found {len(lyca_result['outages'])} outages")
                
                # Save each outage to database
                for outage in lyca_result['outages']:
                    location_text = outage.get('location', '')
                    desc_text = outage.get('description', '')
                    title_text = outage.get('title', f"Incident {outage['incident_id']}")
                    context_text = f"{location_text} {desc_text} {title_text}"
                    
                    from scrapers.common.translation import create_bilingual_text
                    
                    # Create NormalizedOutage object
                    normalized = NormalizedOutage(
                        operator=OperatorEnum.LYCAMOBILE,
                        incident_id=outage['incident_id'],
                        title=create_bilingual_text(title_text),
                        description=create_bilingual_text(desc_text or f"Incident ID: {outage['incident_id']}"),
                        location=location_text or 'Unknown',
                        status=classify_status(context_text, OutageStatus.ACTIVE),
                        severity=SeverityLevel.MEDIUM,
                        affected_services=[s for s in classify_services(context_text) if s.value not in ['voice', 'data']],
                        source_url="https://mboss.telenor.se/coverageportal?appmode=outage",
                        started_at=parse_swedish_date(outage.get('start_time')),
                        estimated_fix_time=parse_swedish_date(outage.get('estimated_end'))
                    )
                    
                    # Geocoding fallback: use county coordinates if specific coords not available
                    # Try location_text first, then context_text if location_text is empty or doesn't match
                    search_text = location_text if location_text else context_text
                    county_name = extract_region_from_text(search_text, SWEDISH_COUNTIES)
                    
                    if county_name:
                        normalized.location = county_name  # Ensure DB holds exact standardization
                        coords = get_county_coordinates(county_name, jitter=True)
                        if coords:
                            normalized.latitude, normalized.longitude = coords
                            logger.info(f"  Geocoded {outage['incident_id']} to {county_name}: {coords}")
                    
                    save_outage(db, normalized, {"source": "lyca_selenium", "raw": outage})
                
                db.commit()
                logger.info(f"Lycamobile: saved {len(lyca_result['outages'])} outages to database")
            else:
                logger.error(f"✗ Lycamobile scraper failed")
                
        except Exception as e:
            logger.error(f"Lycamobile failed with exception: {e}", exc_info=True)
            db.rollback()

        # 3. Tre
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
            
    finally:
        db.close()
    
    logger.info("Scraper run completed.")

if __name__ == "__main__":
    run_scrapers()
