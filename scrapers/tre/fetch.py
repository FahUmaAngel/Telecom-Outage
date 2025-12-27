"""
Tre (3) Sweden scraper.
Extracts data from Next.js state (__NEXT_DATA__).
"""
import requests
import logging
from bs4 import BeautifulSoup
import json
from datetime import datetime
from common.models import OperatorEnum, RawOutage

logger = logging.getLogger(__name__)

TRE_URLS = [
    "https://www.tre.se/varfor-tre/tackning/driftstorningar",
    "https://www.tre.se/varfor-tre/tackning/tackningskarta"
]

class TreFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        
    def fetch_all(self):
        outages = []
        for url in TRE_URLS:
            try:
                logger.info(f"[Tre] Fetching {url}...")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    next_data = soup.find('script', id='__NEXT_DATA__')
                    
                    if next_data:
                        logger.info(f"[Tre] Found __NEXT_DATA__ on {url}")
                        data = json.loads(next_data.string)
                        outages.append(RawOutage(
                            operator=OperatorEnum.TRE,
                            source_url=url,
                            raw_data=data,
                            scraped_at=datetime.utcnow()
                        ))
                    else:
                        logger.warning(f"[Tre] No __NEXT_DATA__ found on {url}")
                else:
                    logger.warning(f"[Tre] Failed to fetch page {url}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"[Tre] Error fetching {url}: {e}")
            
        return outages

def scrape_tre_outages():
    fetcher = TreFetcher()
    return fetcher.fetch_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    outages = scrape_tre_outages()
    print(f"Found {len(outages)} raw data objects")
