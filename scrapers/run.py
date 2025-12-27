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

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ScraperRunner")

def run_scrapers():
    logger.info("Starting scraper run...")
    db = SessionLocal()
    
    try:
        # 1. Telia (with automatic fallback)
        try:
            logger.info("Running Telia (Selenium V3 with Playwright fallback)...")
            from scrapers.telia_scraper import scrape_telia_with_fallback
            from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel, ServiceType
            
            telia_result = scrape_telia_with_fallback()
            
            if telia_result['success']:
                logger.info(f"✓ Telia scraper succeeded using {telia_result['method']}")
                logger.info(f"  Fallback used: {telia_result['fallback_used']}")
                logger.info(f"  Found {len(telia_result['outages'])} outages")
                
                # Save each outage to database
                for outage in telia_result['outages']:
                    # Create NormalizedOutage object
                    normalized = NormalizedOutage(
                        operator=OperatorEnum.TELIA,
                        incident_id=outage['incident_id'],
                        title={
                            "sv": f"Incident {outage['incident_id']}",
                            "en": f"Incident {outage['incident_id']}"
                        },
                        description={
                            "sv": f"Incident ID: {outage['incident_id']}",
                            "en": f"Incident ID: {outage['incident_id']}"
                        },
                        location=outage.get('location', 'Unknown'),
                        status=OutageStatus.ACTIVE,
                        severity=SeverityLevel.MEDIUM,
                        affected_services=[ServiceType.MOBILE],
                        source_url="https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
                    )
                    
                    raw_data = {
                        'source': telia_result['method'],
                        'fallback_used': telia_result['fallback_used'],
                        'raw_outage': outage
                    }
                    
                    save_outage(db, normalized, raw_data)
                
                db.commit()
                logger.info(f"Telia: saved {len(telia_result['outages'])} outages to database")
            else:
                logger.error(f"✗ Telia scraper failed completely")
                logger.error(f"  Errors: {telia_result.get('errors', [])}")
                
        except Exception as e:
            logger.error(f"Telia failed with exception: {e}", exc_info=True)
            db.rollback()

        # 2. Lycamobile
        try:
            logger.info("Running Lycamobile...")
            raw = scrape_lyca_outages()
            parsed = parse_lyca_outages(raw)
            mapped = map_lyca_outages(parsed)
            
            for item in mapped:
                save_outage(db, item, {"source": "lyca_scraper"})
                
            db.commit()
            logger.info(f"Lycamobile: processed {len(mapped)} outages")
        except Exception as e:
            logger.error(f"Lycamobile failed: {e}")
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
