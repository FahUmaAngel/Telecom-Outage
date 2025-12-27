"""
Enhanced Telia scraper using shared Enghouse logic.
"""
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.enghouse import EnghouseFetcher
from common.models import OperatorEnum, RawOutage
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Telia specific config
MOBILE_BASE = "https://coverage.ddc.teliasonera.net/coverageportal_se"
FIXED_BASE = "https://glu2.han.telia.se/bios/glup"

class TeliaFetcher(EnghouseFetcher):
    def __init__(self):
        super().__init__(MOBILE_BASE, OperatorEnum.TELIA)
    
    def fetch_all(self):
        all_outages = []
        
        # 1. Mobile Outages (via Enghouse Base)
        logger.info("[Telia] Fetching mobile messages...")
        all_outages.extend(self.get_messages())
        
        logger.info("[Telia] Fetching mobile area tickets...")
        # Sweden Bounding Box
        sweden_bbox = {
            'llx': 10.0, 'lly': 55.0,
            'urx': 25.0, 'ury': 70.0
        }
        # Telia Services
        services = 'LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA'
        all_outages.extend(self.get_area_tickets(sweden_bbox, services))
        
        # 2. Fixed Outages (GLUP - Custom Logic)
        # GLUP is different from standard Enghouse, keeping custom logic simple here
        logger.info("[Telia] Fetching fixed network outages...")
        all_outages.extend(self._get_fixed_outages())
        
        return all_outages

    def _get_fixed_outages(self):
        outages = []
        try:
            # Counties
            url = f"{FIXED_BASE}?affectedCounties&typeTech=BROADBAND&type=ALL%20VALID"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.text.strip()) > 10:
                outages.append(RawOutage(
                    operator=self.operator,
                    source_url=url,
                    raw_data={'affected_counties': resp.text},
                    scraped_at=datetime.now()
                ))
            
            # Important Info
            url = f"{FIXED_BASE}?importantInfo&typeTech=BROADBAND"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.text.strip()) > 10:
                outages.append(RawOutage(
                    operator=self.operator,
                    source_url=url,
                    raw_data={'important_info': resp.text},
                    scraped_at=datetime.now()
                ))
        except Exception as e:
            logger.error(f"[Telia] Error fetching fixed: {e}")
        return outages

def scrape_telia_outages():
    fetcher = TeliaFetcher()
    return fetcher.fetch_all()

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    outages = scrape_telia_outages()
    print(f"Found {len(outages)} outages")
