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

TRE_URL = "https://www.tre.se/varfor-tre/tackning/driftstorningar"

class TreFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        
    def fetch_all(self):
        outages = []
        try:
            logger.info(f"[Tre] Fetching {TRE_URL}...")
            response = self.session.get(TRE_URL, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                next_data = soup.find('script', id='__NEXT_DATA__')
                
                if next_data:
                    logger.info("[Tre] Found __NEXT_DATA__")
                    data = json.loads(next_data.string)
                    outages.append(RawOutage(
                        operator=OperatorEnum.TRE,
                        source_url=TRE_URL,
                        raw_data=data,
                        scraped_at=datetime.now()
                    ))
                else:
                    logger.warning("[Tre] No __NEXT_DATA__ found")
            else:
                logger.warning(f"[Tre] Failed to fetch page: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[Tre] Error fetching: {e}")
            
        return outages

def scrape_tre_outages():
    fetcher = TreFetcher()
    return fetcher.fetch_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    outages = scrape_tre_outages()
    print(f"Found {len(outages)} raw data objects")
