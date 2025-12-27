
import logging
from tre.fetch import scrape_tre_outages
import json

logging.basicConfig(level=logging.INFO)

outages = scrape_tre_outages()
if outages:
    data = outages[0].raw_data
    with open('tre_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved tre_data.json")
else:
    print("No data found")
