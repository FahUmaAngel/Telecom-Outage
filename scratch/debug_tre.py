import sys
import os
import logging
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.tre.fetch import TreFetcher
from scrapers.tre.parser import parse_tre_outages
from scrapers.tre.mapper import map_tre_outages

logging.basicConfig(level=logging.INFO)

def debug_tre():
    fetcher = TreFetcher()
    raw = fetcher.fetch_all()
    print(f"Raw objects: {len(raw)}")
    
    parsed = parse_tre_outages(raw)
    print(f"Parsed items: {len(parsed)}")
    
    # Let's see some parsed items
    for i, p in enumerate(parsed[:3]):
        print(f"Item {i}: {p['location']} - Start: {p.get('start_time')} - End: {p.get('end_time')}")
        
    normalized = map_tre_outages(parsed)
    print(f"Normalized items: {len(normalized)}")
    
    for i, n in enumerate(normalized[:3]):
        print(f"Norm {i}: {n.incident_id} - {n.location} - {n.status.value}")

if __name__ == "__main__":
    debug_tre()
