import logging
from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages
from scrapers.tre.mapper import map_tre_outages
from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage

logging.basicConfig(level=logging.INFO)

def test_tre():
    print("Fetching Tre...")
    raw = scrape_tre_outages()
    print(f"Got {len(raw)} raw entries")
    parsed = parse_tre_outages(raw)
    print(f"Parsed {len(parsed)} outages")
    mapped = map_tre_outages(parsed)
    print(f"Mapped {len(mapped)} outages")
    
    db = SessionLocal()
    try:
        for item in mapped:
            print(f"Saving {item.incident_id} - {item.title}")
            save_outage(db, item, {"source": "test_tre"})
        db.commit()
        print("Success!")
    finally:
        db.close()

if __name__ == "__main__":
    test_tre()
