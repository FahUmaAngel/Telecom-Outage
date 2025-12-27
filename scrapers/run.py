"""
Main scraper runner.
Executes all scrapers and saves to DB.
"""
import logging
import sys
import os

from scrapers.telia.fetch_enhanced import scrape_telia_outages
from scrapers.telia.parser_enhanced import parse_telia_outages
from scrapers.telia.mapper_enhanced import map_telia_outages

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
        # 1. Telia
        try:
            logger.info("Running Telia...")
            raw = scrape_telia_outages()
            parsed = parse_telia_outages(raw)
            mapped = map_telia_outages(parsed)
            
            for item in mapped:
                # Find corresponding raw data dict
                # In a real scenario we'd map this better, for now just using empty dict or trying to pass it through
                # The mapper consumes raw_data but doesn't output it directly
                # We'll save the normalized object, raw_data handling might need refactoring to pass through
                # For Phase 1, we store the full raw response in CRUD if we can, 
                # but our `save_outage` expects a dict.
                # Let's just store a simple metadata dict for now if unavailable
                save_outage(db, item, {"source": "telia_scraper"})
                
            db.commit()
            logger.info(f"Telia: processed {len(mapped)} outages")
        except Exception as e:
            logger.error(f"Telia failed: {e}")
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
