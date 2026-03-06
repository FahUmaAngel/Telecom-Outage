import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.mapper import map_tre_outages
from scrapers.db.crud import save_outage
from scrapers.common.models import OperatorEnum
from scrapers.db.connection import SessionLocal

logging.basicConfig(level=logging.INFO)

print("Fetching Tre outages...")
raw_data = scrape_tre_outages()
print(f"Fetched {len(raw_data)} raw pages.")

if raw_data:
    print("Parsing Tre outages...")
    from scrapers.tre.parser import parse_tre_outages
    parsed = parse_tre_outages(raw_data)
    print(f"Parsed {len(parsed)} outages.")
    
    print("Mapping to normalized format...")
    mapped = map_tre_outages(parsed)
    print(f"Mapped {len(mapped)} outages.")
    
    print("Saving to database...")
    db = SessionLocal()
    try:
        saved = 0
        for item in mapped:
            save_outage(db, item, {"source": "tre_standalone"})
            saved += 1
        db.commit()
        print(f"Successfully saved {saved} Tre outages to DB.")
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
    finally:
        db.close()
    
    print("Done!")
else:
    print("No data fetched.")
