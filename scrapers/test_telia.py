"""
Main test script for Telia scraper.
Tests the complete pipeline: fetch -> parse -> map
"""
import logging
import sys
from pathlib import Path

# Add scrapers directory to path
sys.path.insert(0, str(Path(__file__).parent))

from telia.fetch import fetch_telia_outages
from telia.parser import parse_telia_html
from telia.mapper import map_to_standard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_telia_scraper():
    """Test the complete Telia scraper pipeline."""
    logger.info("=" * 60)
    logger.info("Testing Telia Scraper Pipeline")
    logger.info("=" * 60)
    
    # Step 1: Fetch data
    logger.info("\n[1/3] Fetching data from Telia...")
    html_content = fetch_telia_outages()
    
    if not html_content:
        logger.error("✗ Failed to fetch data from Telia")
        return False
    
    logger.info(f"✓ Successfully fetched {len(html_content)} bytes")
    
    # Save raw HTML for inspection
    output_file = Path(__file__).parent / "telia_raw_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"✓ Saved raw HTML to: {output_file}")
    
    # Step 2: Parse data
    logger.info("\n[2/3] Parsing HTML content...")
    raw_outages = parse_telia_html(html_content)
    
    logger.info(f"✓ Parsed {len(raw_outages)} potential outages")
    
    if raw_outages:
        logger.info("\nSample raw outage data:")
        for i, outage in enumerate(raw_outages[:3], 1):
            logger.info(f"\n  Outage {i}:")
            for key, value in outage.items():
                if key != 'raw_html':  # Skip raw HTML in logs
                    logger.info(f"    {key}: {value[:100] if isinstance(value, str) else value}")
    
    # Step 3: Map to standard format
    logger.info("\n[3/3] Mapping to standard format...")
    normalized_outages = map_to_standard(raw_outages)
    
    logger.info(f"✓ Mapped {len(normalized_outages)} outages to standard format")
    
    if normalized_outages:
        logger.info("\nNormalized outages:")
        for i, outage in enumerate(normalized_outages, 1):
            logger.info(f"\n  Outage {i}:")
            logger.info(f"    Operator: {outage.operator}")
            logger.info(f"    Title: {outage.title}")
            logger.info(f"    Location: {outage.location}")
            logger.info(f"    Status: {outage.status}")
            logger.info(f"    Severity: {outage.severity}")
            logger.info(f"    Services: {', '.join(outage.affected_services)}")
            if outage.description:
                logger.info(f"    Description: {outage.description[:100]}...")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    logger.info(f"  - Fetched: {len(html_content)} bytes")
    logger.info(f"  - Parsed: {len(raw_outages)} raw outages")
    logger.info(f"  - Normalized: {len(normalized_outages)} outages")
    logger.info("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_telia_scraper()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
