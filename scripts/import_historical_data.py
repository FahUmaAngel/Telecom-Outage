import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator, Region
from scrapers.historical_scraper import scrape_telia_history, scrape_telenor_current, scrape_tre_current
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("HistoricalImporter")

SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]

def clean_date(date_str):
    if not date_str:
        return None
    try:
        # Some are just '2025-01-01', others have time
        dt = date_parser.parse(date_str)
        return dt
    except Exception:
        return None

def import_historical_data():
    db = SessionLocal()
    try:
        # Cache operators
        operators = {op.name.lower(): op.id for op in db.query(Operator).all()}
        
        # Cache regions
        regions = db.query(Region).all()
        region_map = {}
        for r in regions:
            if isinstance(r.name, dict):
                sv_name = r.name.get('sv', '')
                if sv_name:
                    region_map[sv_name.lower()] = r.id
            elif isinstance(r.name, str):
                try:
                    name_dict = json.loads(r.name)
                    sv_name = name_dict.get('sv', '')
                    if sv_name:
                        region_map[sv_name.lower()] = r.id
                except:
                    region_map[r.name.lower()] = r.id

        # 1. Scrape Telia
        logger.info("Scraping Telia Historical Data...")
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        telia_res = scrape_telia_history(start_date, end_date)
        
        # 2. Scrape Telenor
        logger.info("Scraping Telenor Current Data...")
        telenor_res = scrape_telenor_current()
        
        # 3. Scrape Tre
        logger.info("Scraping Tre Current Data...")
        tre_res = scrape_tre_current()
        
        all_incidents = (
            telia_res.get('outages', []) + 
            telenor_res.get('outages', []) + 
            tre_res.get('outages', [])
        )
        
        logger.info(f"Total incidents collected: {len(all_incidents)}")
        
        new_inserted = 0
        updated = 0
        
        for inc in all_incidents:
            op_name = inc.get('operator', '').lower()
            if not op_name:
                continue
                
            op_id = operators.get(op_name)
            if not op_id:
                logger.warning(f"Operator {op_name} not found in DB")
                continue
                
            location = inc.get('location', '')
            region_id = None
            if location:
                # Find matching region
                for r_name, r_id in region_map.items():
                    if r_name.replace(' län', '') in location.lower():
                        region_id = r_id
                        break
            
            start_dt = clean_date(inc.get('start_time'))
            end_dt = clean_date(inc.get('estimated_end'))
            
            # Bilingual JSON for title/desc
            title_json = {"sv": inc.get('title', ''), "en": inc.get('title', '')}
            desc_json = {"sv": inc.get('description', ''), "en": inc.get('description', '')}
            
            existing = db.query(Outage).filter(Outage.incident_id == inc['incident_id'], Outage.operator_id == op_id).first()
            
            if existing:
                existing.status = inc.get('status', 'resolved')
                existing.start_time = start_dt or existing.start_time
                if existing.status == 'resolved':
                    existing.end_time = end_dt or existing.end_time
                else:
                    existing.estimated_fix_time = end_dt or existing.estimated_fix_time
                existing.region_id = region_id or existing.region_id
                existing.location = location or existing.location
                updated += 1
            else:
                new_outage = Outage(
                    incident_id=inc['incident_id'],
                    operator_id=op_id,
                    region_id=region_id,
                    title=title_json,
                    description=desc_json,
                    status=inc.get('status', 'resolved'),
                    severity='medium',
                    start_time=start_dt,
                    end_time=end_dt if inc.get('status') == 'resolved' else None,
                    estimated_fix_time=end_dt if inc.get('status') != 'resolved' else None,
                    location=location,
                    affected_services=["4g"]
                )
                db.add(new_outage)
                new_inserted += 1
                
        db.commit()
        logger.info(f"Done. Inserted: {new_inserted}, Updated: {updated}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_historical_data()
