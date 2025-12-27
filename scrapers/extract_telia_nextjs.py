"""
Extract Next.js embedded data from Telia's main outage page.
The page embeds JSON data in a script tag that we can parse.
"""
import requests
import json
import re
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


def extract_nextjs_data(html_content):
    """Extract Next.js __NEXT_DATA__ from HTML."""
    try:
        # Find the __NEXT_DATA__ script tag
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html_content, re.DOTALL)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            logger.info("✓ Successfully extracted __NEXT_DATA__")
            return data
        else:
            logger.warning("Could not find __NEXT_DATA__ in HTML")
            return None
    except Exception as e:
        logger.error(f"Error extracting Next.js data: {e}")
        return None


def fetch_and_parse_telia():
    """Fetch Telia page and extract outage data."""
    
    # Test both mobile and fixed network categories
    categories = [
        ('mobila-natet', 'Mobile Network'),
        ('fasta-natet', 'Fixed Network')
    ]
    
    all_outages = []
    
    for category, name in categories:
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching: {name}")
        logger.info(f"{'='*60}")
        
        url = f"https://www.telia.se/foretag/support/driftinformation"
        params = {'category': category}
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            response.raise_for_status()
            
            logger.info(f"✓ Fetched {len(response.text)} bytes")
            
            # Extract Next.js data
            next_data = extract_nextjs_data(response.text)
            
            if next_data:
                # Save the full data structure for inspection
                output_file = f"telia_{category}_nextjs_data.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(next_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ Saved Next.js data to: {output_file}")
                
                # Try to find outage data in the structure
                page_props = next_data.get('props', {}).get('pageProps', {})
                
                logger.info(f"\nPage Props Keys: {list(page_props.keys())}")
                
                # Look for outage-related data
                for key, value in page_props.items():
                    if isinstance(value, (list, dict)):
                        logger.info(f"\n{key}: {type(value)}")
                        if isinstance(value, list):
                            logger.info(f"  Length: {len(value)}")
                            if len(value) > 0:
                                logger.info(f"  Sample: {json.dumps(value[0], indent=2, ensure_ascii=False)[:300]}")
                        elif isinstance(value, dict):
                            logger.info(f"  Keys: {list(value.keys())}")
                
                all_outages.append({
                    'category': category,
                    'name': name,
                    'data': next_data
                })
            
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
    
    return all_outages


def main():
    logger.info("="*60)
    logger.info("Telia Next.js Data Extractor")
    logger.info("="*60)
    
    outages = fetch_and_parse_telia()
    
    # Save combined results
    output_file = "telia_nextjs_extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(outages, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ All results saved to: {output_file}")


if __name__ == "__main__":
    main()
