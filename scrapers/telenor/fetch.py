"""
Telenor scraper using shared Enghouse logic.
"""
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.enghouse import EnghouseFetcher
from common.models import OperatorEnum

logger = logging.getLogger(__name__)

# Telenor Endpoint
TELENOR_BASE = "https://mboss.telenor.se/coverageportal"

class TelenorFetcher(EnghouseFetcher):
    def __init__(self):
        super().__init__(TELENOR_BASE, OperatorEnum.TELENOR, token_param='rt')
    
    def fetch_all(self):
        all_outages = []
        
        logger.info("[Telenor] Fetching messages...")
        all_outages.extend(self.get_messages())
        
        logger.info("[Telenor] Fetching area tickets...")
        # Sweden Bounding Box
        sweden_bbox = {
            'llx': 10.0, 'lly': 55.0,
            'urx': 25.0, 'ury': 70.0
        }
        # Telenor Services
        services = 'GSM_VOICE,GSM_DATA,UMTS_VOICE,UMTS_DATA,LTE_VOICE,LTE_DATA,5G_DATA,VoLTE'
        all_outages.extend(self.get_area_tickets(sweden_bbox, services))
        
        return all_outages

def scrape_telenor_outages():
    fetcher = TelenorFetcher()
    return fetcher.fetch_all()

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    outages = scrape_telenor_outages()
    print(f"Found {len(outages)} outages")
