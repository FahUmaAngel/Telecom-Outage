
import json
import logging
from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages

logging.basicConfig(level=logging.INFO)

def test_tre():
    raw_outages = scrape_tre_outages()
    print(f"Fetched {len(raw_outages)} raw objects")
    
    parsed = parse_tre_outages(raw_outages)
    print(f"Parsed {len(parsed)} outages")
    
    for i, outage in enumerate(parsed):
        print(f"--- Outage {i+1} ---")
        print(f"ID: {outage.get('id')}")
        print(f"Location: {outage.get('location')}")
        print(f"Start: {outage.get('start_time')}")
        print(f"End: {outage.get('end_time')}")
        print(f"Services: {outage.get('affected_services')}")
        # print(f"Description: {outage.get('description')}")

if __name__ == "__main__":
    test_tre()
