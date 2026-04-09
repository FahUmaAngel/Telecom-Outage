import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages
import json
import logging

logging.basicConfig(level=logging.INFO)

raw_data = scrape_tre_outages()
print(f"Fetched {len(raw_data)} raw Tre pages.")

if raw_data:
    first_page_meta = {k: v for k, v in raw_data[0].__dict__.items() if k != 'raw_data'}
    print(f"Sample raw document metadata: {first_page_meta}")
    
    # Try parsing
    parsed = parse_tre_outages(raw_data)
    print(f"Parsed {len(parsed)} outages.")
    if parsed:
        print(json.dumps(parsed[0], indent=2))
else:
    print("No raw data fetched.")
