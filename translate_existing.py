import sys
import os
import json
import logging
from sqlalchemy import select, update

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage
from scrapers.common.translation import translate_swedish_to_english

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranslateMaintenance")

def translate_all():
    db = SessionLocal()
    try:
        # Fetch all outages
        outages = db.query(Outage).all()
        logger.info(f"Found {len(outages)} outages to process.")
        
        updated_count = 0
        for outage in outages:
            needs_update = False
            
            # Use copies to avoid direct reference issues with SQLAlchemy JSON
            description = dict(outage.description) if outage.description else None
            title = dict(outage.title) if outage.title else None
            
            # Check description
            if description and isinstance(description, dict):
                sv_desc = description.get('sv', '')
                en_desc = description.get('en', '')
                
                # If Swedish exists, try to re-translate
                if sv_desc:
                    new_en = translate_swedish_to_english(sv_desc)
                    if new_en != en_desc:
                        description['en'] = new_en
                        outage.description = description
                        needs_update = True
                        
            # Check title
            if title and isinstance(title, dict):
                sv_title = title.get('sv', '')
                en_title = title.get('en', '')
                
                if sv_title:
                    new_en_title = translate_swedish_to_english(sv_title)
                    if new_en_title != en_title:
                        title['en'] = new_en_title
                        outage.title = title
                        needs_update = True
            
            if needs_update:
                from sqlalchemy.orm.attributes import flag_modified
                if outage.description: flag_modified(outage, "description")
                if outage.title: flag_modified(outage, "title")
                updated_count += 1
                
        db.commit()
        logger.info(f"Successfully updated/translated {updated_count} outages.")
        
    except Exception as e:
        logger.error(f"Error during translation maintenance: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    translate_all()
