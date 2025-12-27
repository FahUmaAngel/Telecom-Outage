import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telia.fetch_enhanced import TeliaFetcher
from lycamobile.fetch import LycamobileFetcher

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_telia():
    logger.info("--- Testing Telia ---")
    fetcher = TeliaFetcher()
    token = fetcher.get_token()
    logger.info(f"Telia Token: {token}")
    
    messages = fetcher.get_messages()
    logger.info(f"Telia Messages: {len(messages)}")
    
    # Sweden Bounding Box
    bbox = {'llx': 10.0, 'lly': 55.0, 'urx': 25.0, 'ury': 70.0}
    services = 'LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA'
    tickets = fetcher.get_area_tickets(bbox, services)
    logger.info(f"Telia Area Tickets: {len(tickets)}")

def test_lyca():
    logger.info("--- Testing Lycamobile ---")
    fetcher = LycamobileFetcher()
    token = fetcher.get_token()
    logger.info(f"Lyca Token: {token}")
    
    messages = fetcher.get_messages()
    logger.info(f"Lyca Messages: {len(messages)}")
    
    bbox = {'llx': 10.0, 'lly': 55.0, 'urx': 25.0, 'ury': 70.0}
    services = 'GSM_VOICE,GSM_DATA,UMTS_VOICE,UMTS_DATA,LTE_VOICE,LTE_DATA,5G_DATA'
    tickets = fetcher.get_area_tickets(bbox, services)
    logger.info(f"Lyca Area Tickets: {len(tickets)}")

if __name__ == "__main__":
    test_telia()
    print("\n")
    test_lyca()
