"""
Integration test for ALL scrapers: Telia, Tre, Lycamobile.
"""
import logging
import json
from telia.fetch_enhanced import scrape_telia_outages
from telia.parser_enhanced import parse_telia_outages
from telia.mapper_enhanced import map_telia_outages

from lycamobile.fetch import scrape_lyca_outages
from lycamobile.parser import parse_lyca_outages
from lycamobile.mapper import map_lyca_outages

from tre.fetch import scrape_tre_outages
from tre.parser import parse_tre_outages
from tre.mapper import map_tre_outages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestAll")

def test_everything():
    all_results = []
    
    # 1. Telia
    try:
        logger.info("\n=== Testing TELIA ===")
        raw_telia = scrape_telia_outages()
        parsed_telia = parse_telia_outages(raw_telia)
        mapped_telia = map_telia_outages(parsed_telia)
        logger.info(f"Telia: {len(mapped_telia)} normalized outages")
        all_results.extend([m.model_dump() for m in mapped_telia])
    except Exception as e:
        logger.error(f"Telia Failed: {e}")

    # 2. Lycamobile
    try:
        logger.info("\n=== Testing LYCAMOBILE ===")
        raw_lyca = scrape_lyca_outages()
        parsed_lyca = parse_lyca_outages(raw_lyca)
        mapped_lyca = map_lyca_outages(parsed_lyca)
        logger.info(f"Lycamobile: {len(mapped_lyca)} normalized outages")
        all_results.extend([m.model_dump() for m in mapped_lyca])
    except Exception as e:
        logger.error(f"Lycamobile Failed: {e}")

    # 3. Tre
    try:
        logger.info("\n=== Testing TRE ===")
        raw_tre = scrape_tre_outages()
        parsed_tre = parse_tre_outages(raw_tre)
        mapped_tre = map_tre_outages(parsed_tre)
        logger.info(f"Tre: {len(mapped_tre)} normalized outages")
        all_results.extend([m.model_dump() for m in mapped_tre])
    except Exception as e:
        logger.error(f"Tre Failed: {e}")

    # Save all
    with open('all_outages_result.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\nSaved {len(all_results)} total outages to all_outages_result.json")

if __name__ == "__main__":
    test_everything()
