"""
Updated Telia Scraper - Final Version
Integrates multiple approaches to reliably extract outage data.
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

# Main outage page URL (iframe source)
OUTAGE_PAGE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    "Referer": "https://www.telia.se/",
}


def extract_incident_ids_from_html(html_content: str) -> List[str]:
    """Extract incident IDs (INCSE followed by numbers) from HTML."""
    pattern = r'INCSE\d+'
    incidents = re.findall(pattern, html_content)
    return list(set(incidents))  # Remove duplicates


def extract_regions_from_html(html_content: str) -> List[str]:
    """Extract Swedish county names (län) from HTML."""
    pattern = r'([A-ZÅÄÖ][a-zåäö]+(?:\s+[a-zåäö]+)*\s+län)'
    regions = re.findall(pattern, html_content)
    return list(set(regions))


def parse_outage_details(html_content: str) -> List[Dict]:
    """
    Parse outage details from HTML content.
    Looks for patterns like:
    - Incident ID: INCSE0425370
    - Dates: Sat, Dec 27, 22:44
    - Status information
    """
    outages = []
    
    # Find all incident IDs
    incident_ids = extract_incident_ids_from_html(html_content)
    
    for inc_id in incident_ids:
        outage = {
            'incident_id': inc_id,
            'operator': 'Telia',
            'source': 'coverage_portal',
            'status': 'active',
            'affected_services': [],
            'location': None,
            'start_time': None,
            'estimated_end': None,
        }
        
        # Try to find context around this incident ID
        # Look for the incident in the HTML and extract surrounding text
        pattern = rf'{inc_id}[^<]*(?:<[^>]+>[^<]*)*'
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        if matches:
            context = matches[0][:500]  # Get up to 500 chars of context
            
            # Look for date patterns
            date_pattern = r'(\w+,\s+\w+\s+\d+,\s+\d{2}:\d{2})'
            dates = re.findall(date_pattern, context)
            if dates:
                outage['start_time'] = dates[0] if len(dates) > 0 else None
                outage['estimated_end'] = dates[1] if len(dates) > 1 else None
            
            # Look for service types
            if 'mobilnät' in context.lower() or 'mobile' in context.lower():
                outage['affected_services'].append('mobile')
            if 'bredband' in context.lower() or 'broadband' in context.lower():
                outage['affected_services'].append('broadband')
        
        outages.append(outage)
    
    return outages


def scrape_telia_outages() -> Dict:
    """
    Main scraper function.
    Fetches the outage page and extracts incident information.
    """
    logger.info("="*60)
    logger.info("Telia Outage Scraper - Final Version")
    logger.info("="*60)
    
    results = {
        'outages': [],
        'regions_affected': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'source': 'coverage_portal'
    }
    
    try:
        logger.info(f"Fetching outage page: {OUTAGE_PAGE_URL}")
        response = requests.get(OUTAGE_PAGE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        html_content = response.text
        logger.info(f"✓ Fetched {len(html_content)} bytes")
        
        # Save HTML for debugging
        with open('telia_outage_final.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info("✓ Saved HTML to telia_outage_final.html")
        
        # Extract incident IDs
        incident_ids = extract_incident_ids_from_html(html_content)
        logger.info(f"✓ Found {len(incident_ids)} incident IDs: {incident_ids}")
        
        # Extract affected regions
        regions = extract_regions_from_html(html_content)
        logger.info(f"✓ Found {len(regions)} affected regions: {regions}")
        results['regions_affected'] = regions
        
        # Parse detailed outage information
        outages = parse_outage_details(html_content)
        results['outages'] = outages
        
        # Use BeautifulSoup for more structured parsing
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for specific patterns in the page
        # The page might have divs or sections with outage information
        for outage in results['outages']:
            # Try to find location information
            for region in regions:
                if region.lower() in html_content.lower():
                    # This is a simple heuristic - in production, you'd want more sophisticated matching
                    if not outage['location']:
                        outage['location'] = region
        
        results['success'] = len(results['outages']) > 0
        
    except Exception as e:
        logger.error(f"Error scraping Telia outages: {e}", exc_info=True)
        results['error'] = str(e)
    
    logger.info("\n" + "="*60)
    logger.info(f"Scraping completed: {'SUCCESS' if results['success'] else 'FAILED'}")
    logger.info(f"Total outages: {len(results['outages'])}")
    logger.info(f"Affected regions: {len(results['regions_affected'])}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    # Run the scraper
    results = scrape_telia_outages()
    
    # Save results
    output_file = "telia_outages_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    
    # Display results
    if results['outages']:
        logger.info("\n📊 Outages found:")
        for outage in results['outages']:
            logger.info(f"\n  Incident: {outage['incident_id']}")
            logger.info(f"    Location: {outage.get('location', 'Unknown')}")
            logger.info(f"    Start: {outage.get('start_time', 'Unknown')}")
            logger.info(f"    Est. End: {outage.get('estimated_end', 'Unknown')}")
            logger.info(f"    Services: {', '.join(outage['affected_services']) if outage['affected_services'] else 'Unknown'}")
    
    if results['regions_affected']:
        logger.info("\n📍 Affected regions:")
        for region in results['regions_affected']:
            logger.info(f"  - {region}")
    
    if not results['success']:
        logger.warning("\n⚠️ No outage data found")
        logger.info("Note: The page may require JavaScript rendering.")
        logger.info("For full functionality, use the Selenium scraper: telia_selenium_scraper.py")
