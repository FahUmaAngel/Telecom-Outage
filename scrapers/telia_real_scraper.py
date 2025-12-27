"""
Real Telia Scraper using discovered API endpoints.
Based on manual investigation findings.
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Endpoints discovered through manual investigation
MOBILE_COVERAGE_BASE = "https://coverage.ddc.teliasonera.net/coverageportal_se"
FIXED_NETWORK_BASE = "https://glu2.han.telia.se/bios/glup"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    "Referer": "https://www.telia.se/",
}


def get_mobile_outages() -> List[Dict]:
    """
    Fetch mobile network outages from CellVision CoveragePortal.
    
    Returns:
        List of mobile outage dictionaries
    """
    outages = []
    
    try:
        # First, get the list of affected counties/regions
        # This endpoint returns which regions have active outages
        url = f"{MOBILE_COVERAGE_BASE}/Fault/FaultsLastUpdatedInfo"
        
        logger.info(f"Fetching mobile outage info from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✓ Mobile outage info retrieved (Status: {response.status_code})")
            
            # The actual outage details require AreaTicketList endpoint
            # This needs bounding box coordinates and service types
            # For now, we'll try a broad request
            
            # Example parameters from investigation:
            # llx, lly, urx, ury = bounding box coordinates
            # services = LTE700_DATA, etc.
            # ert = session token
            
            # Since we need session token, let's try alternative approach
            # Get important messages which might contain outage info
            messages_url = f"{MOBILE_COVERAGE_BASE}/ImportantMessages/GetMessages"
            msg_response = requests.get(messages_url, headers=HEADERS, timeout=10)
            
            if msg_response.status_code == 200:
                messages = msg_response.json()
                logger.info(f"✓ Retrieved {len(messages) if isinstance(messages, list) else 'some'} important messages")
                
                if isinstance(messages, list):
                    for msg in messages:
                        outages.append({
                            'type': 'mobile',
                            'source': 'important_messages',
                            'data': msg
                        })
        else:
            logger.warning(f"Failed to fetch mobile outages: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching mobile outages: {e}")
    
    return outages


def get_fixed_network_outages() -> List[Dict]:
    """
    Fetch fixed network (broadband) outages from GLUP system.
    
    Returns:
        List of fixed network outage dictionaries
    """
    outages = []
    
    try:
        # Get affected counties for broadband
        url = f"{FIXED_NETWORK_BASE}?affectedCounties&typeTech=BROADBAND&type=ALL%20VALID"
        
        logger.info(f"Fetching fixed network outages from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.text
            logger.info(f"✓ Fixed network data retrieved (Status: {response.status_code})")
            logger.info(f"  Response length: {len(data)} bytes")
            
            # Parse the response
            # The response format needs to be determined from actual data
            outages.append({
                'type': 'fixed',
                'source': 'affected_counties',
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            
            # Also try to get important info
            info_url = f"{FIXED_NETWORK_BASE}?importantInfo&typeTech=BROADBAND"
            info_response = requests.get(info_url, headers=HEADERS, timeout=10)
            
            if info_response.status_code == 200:
                logger.info(f"✓ Retrieved important info for fixed network")
                outages.append({
                    'type': 'fixed',
                    'source': 'important_info',
                    'data': info_response.text,
                    'timestamp': datetime.now().isoformat()
                })
        else:
            logger.warning(f"Failed to fetch fixed network outages: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching fixed network outages: {e}")
    
    return outages


def scrape_all_telia_outages() -> Dict:
    """
    Scrape all Telia outages from both mobile and fixed networks.
    
    Returns:
        Dictionary with mobile and fixed network outages
    """
    logger.info("=" * 60)
    logger.info("Starting Telia Outage Scraper (Real API)")
    logger.info("=" * 60)
    
    results = {
        'mobile': [],
        'fixed': [],
        'timestamp': datetime.now().isoformat(),
        'success': False
    }
    
    # Fetch mobile outages
    logger.info("\n[1/2] Fetching mobile network outages...")
    results['mobile'] = get_mobile_outages()
    logger.info(f"  Found {len(results['mobile'])} mobile outage entries")
    
    # Fetch fixed network outages
    logger.info("\n[2/2] Fetching fixed network outages...")
    results['fixed'] = get_fixed_network_outages()
    logger.info(f"  Found {len(results['fixed'])} fixed network outage entries")
    
    # Mark as successful if we got any data
    results['success'] = len(results['mobile']) > 0 or len(results['fixed']) > 0
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Scraping completed: {'SUCCESS' if results['success'] else 'NO DATA'}")
    logger.info(f"Total entries: {len(results['mobile']) + len(results['fixed'])}")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    import json
    
    # Run the scraper
    results = scrape_all_telia_outages()
    
    # Save results
    output_file = "telia_real_api_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    # Display summary
    if results['success']:
        print("\n📊 Summary:")
        print(f"  Mobile outages: {len(results['mobile'])}")
        print(f"  Fixed outages: {len(results['fixed'])}")
        
        if results['mobile']:
            print("\n📱 Mobile outage sample:")
            print(json.dumps(results['mobile'][0], indent=2, ensure_ascii=False)[:500])
        
        if results['fixed']:
            print("\n🏠 Fixed outage sample:")
            print(json.dumps(results['fixed'][0], indent=2, ensure_ascii=False)[:500])
    else:
        print("\n⚠️ No outage data found")
