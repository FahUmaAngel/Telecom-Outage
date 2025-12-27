"""
Updated Telia Scraper - Targets the actual iframe endpoint.
Based on browser investigation findings.
"""
import requests
import json
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The actual endpoint that contains outage data (discovered via browser investigation)
COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
FAULT_API_URL = f"{COVERAGE_PORTAL_URL}/Fault/AreaTicketList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    "Referer": "https://www.telia.se/",
}


def fetch_outage_page() -> Optional[str]:
    """
    Fetch the main outage page HTML which contains embedded data.
    """
    try:
        url = f"{COVERAGE_PORTAL_URL}?appmode=outage"
        logger.info(f"Fetching outage page from: {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        logger.info(f"✓ Fetched {len(response.text)} bytes")
        return response.text
        
    except Exception as e:
        logger.error(f"Error fetching outage page: {e}")
        return None


def extract_outages_from_html(html_content: str) -> List[Dict]:
    """
    Extract outage data from the HTML page.
    The page contains JavaScript data that we can parse.
    """
    outages = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for script tags that might contain outage data
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'fault' in script.string.lower():
                # Try to extract JSON data from JavaScript
                # Look for patterns like: var faults = [...] or faults: [...]
                content = script.string
                
                # Try to find JSON arrays or objects
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, dict) and any(key in str(data).lower() for key in ['fault', 'incident', 'outage']):
                            outages.append(data)
                    except:
                        pass
        
        logger.info(f"Extracted {len(outages)} outages from HTML")
        
    except Exception as e:
        logger.error(f"Error extracting outages from HTML: {e}")
    
    return outages


def fetch_fault_api(bbox: Dict = None) -> List[Dict]:
    """
    Try to fetch faults directly from the API endpoint.
    
    Args:
        bbox: Bounding box coordinates (llx, lly, urx, ury)
    """
    try:
        # Default to Sweden's approximate bounding box
        if bbox is None:
            bbox = {
                'llx': '10.0',   # West
                'lly': '55.0',   # South
                'urx': '25.0',   # East
                'ury': '70.0',   # North
            }
        
        params = {
            **bbox,
            'services': 'LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,UMTS900_DATA,UMTS2100_DATA',
        }
        
        logger.info(f"Fetching faults from API: {FAULT_API_URL}")
        response = requests.get(FAULT_API_URL, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"✓ API returned JSON data")
                return data if isinstance(data, list) else [data]
            except:
                logger.warning(f"API returned non-JSON data: {len(response.text)} bytes")
                return []
        else:
            logger.warning(f"API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching fault API: {e}")
        return []


def scrape_telia_outages() -> Dict:
    """
    Main scraper function - tries multiple methods to get outage data.
    """
    logger.info("="*60)
    logger.info("Telia Outage Scraper (Updated)")
    logger.info("="*60)
    
    results = {
        'outages': [],
        'source': None,
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    # Method 1: Try the fault API directly
    logger.info("\n[Method 1] Trying fault API...")
    api_outages = fetch_fault_api()
    if api_outages:
        results['outages'].extend(api_outages)
        results['source'] = 'fault_api'
        results['success'] = True
        logger.info(f"✓ Found {len(api_outages)} outages from API")
    
    # Method 2: Fetch and parse the HTML page
    if not results['success']:
        logger.info("\n[Method 2] Parsing HTML page...")
        html = fetch_outage_page()
        if html:
            # Save HTML for debugging
            with open('telia_outage_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info("✓ Saved HTML to telia_outage_page.html")
            
            html_outages = extract_outages_from_html(html)
            if html_outages:
                results['outages'].extend(html_outages)
                results['source'] = 'html_parsing'
                results['success'] = True
                logger.info(f"✓ Found {len(html_outages)} outages from HTML")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info(f"Scraping completed: {'SUCCESS' if results['success'] else 'NO DATA'}")
    logger.info(f"Total outages: {len(results['outages'])}")
    logger.info(f"Source: {results['source']}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    # Run the scraper
    results = scrape_telia_outages()
    
    # Save results
    output_file = "telia_outages_updated.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    
    # Display sample
    if results['outages']:
        logger.info("\n📊 Sample outage data:")
        logger.info(json.dumps(results['outages'][0], indent=2, ensure_ascii=False)[:500])
    else:
        logger.info("\n⚠️ No outage data found")
        logger.info("\nNOTE: The outage data might be loaded dynamically via JavaScript.")
        logger.info("Consider using Selenium/Playwright for JavaScript-heavy pages.")
