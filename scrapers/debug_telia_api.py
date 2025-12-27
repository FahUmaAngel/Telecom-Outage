"""
Debug script to test various Telia API endpoints and parameters.
This will help identify which endpoints return actual outage data.
"""
import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    "Referer": "https://www.telia.se/",
}


def test_endpoint(name, url, method="GET", params=None, json_data=None):
    """Test a single API endpoint and log results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {name}")
    logger.info(f"URL: {url}")
    if params:
        logger.info(f"Params: {params}")
    logger.info(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        else:
            response = requests.post(url, headers=HEADERS, json=json_data, timeout=10)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        logger.info(f"Content-Length: {len(response.content)} bytes")
        
        # Try to parse as JSON
        try:
            data = response.json()
            logger.info(f"✓ Valid JSON response")
            logger.info(f"JSON Preview: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
            return {"success": True, "data": data, "type": "json"}
        except:
            # Not JSON, check if it's HTML or text
            text = response.text
            logger.info(f"Text Preview (first 300 chars): {text[:300]}")
            
            # Check if empty or whitespace only
            if text.strip():
                logger.info(f"✓ Non-empty text response")
                return {"success": True, "data": text, "type": "text"}
            else:
                logger.warning(f"⚠ Empty or whitespace-only response")
                return {"success": False, "data": None, "type": "empty"}
                
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Test all known Telia API endpoints."""
    results = {}
    
    # Test 1: Mobile Coverage Portal - Fault Info
    results['mobile_fault_info'] = test_endpoint(
        "Mobile Fault Info",
        "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/FaultsLastUpdatedInfo"
    )
    
    # Test 2: Mobile Coverage Portal - Important Messages
    results['mobile_messages'] = test_endpoint(
        "Mobile Important Messages",
        "https://coverage.ddc.teliasonera.net/coverageportal_se/ImportantMessages/GetMessages"
    )
    
    # Test 3: Mobile Coverage Portal - Area Tickets (requires parameters)
    # Try with broad Sweden coordinates
    results['mobile_area_tickets'] = test_endpoint(
        "Mobile Area Tickets",
        "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/AreaTicketList",
        params={
            'llx': '10.0',  # Lower left X (longitude)
            'lly': '55.0',  # Lower left Y (latitude)
            'urx': '25.0',  # Upper right X
            'ury': '70.0',  # Upper right Y
            'services': 'LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA',
        }
    )
    
    # Test 4: Fixed Network - Affected Counties
    results['fixed_affected_counties'] = test_endpoint(
        "Fixed Network - Affected Counties",
        "https://glu2.han.telia.se/bios/glup/glup.html",
        params={
            'affectedCounties': '',
            'typeTech': 'BROADBAND',
            'type': 'ALL VALID'
        }
    )
    
    # Test 5: Fixed Network - Important Info
    results['fixed_important_info'] = test_endpoint(
        "Fixed Network - Important Info",
        "https://glu2.han.telia.se/bios/glup/glup.html",
        params={
            'importantInfo': '',
            'typeTech': 'BROADBAND'
        }
    )
    
    # Test 6: Try the main Telia page API (Next.js data)
    results['nextjs_mobile_data'] = test_endpoint(
        "Next.js Mobile Network Data",
        "https://www.telia.se/_next/data/buildId/foretag/support/driftinformation.json",
        params={'category': 'mobila-natet'}
    )
    
    # Test 7: Try alternative GLUP endpoint
    results['glup_all_faults'] = test_endpoint(
        "GLUP All Faults",
        "https://glu2.han.telia.se/bios/glup/glup.html",
        params={
            'allFaults': '',
            'typeTech': 'ALL',
            'type': 'ALL VALID'
        }
    )
    
    # Test 8: Try to get fault details
    results['glup_fault_details'] = test_endpoint(
        "GLUP Fault Details",
        "https://glu2.han.telia.se/bios/glup/glup.html",
        params={
            'faultDetails': '',
            'typeTech': 'BROADBAND'
        }
    )
    
    # Test 9: Coverage portal session/config
    results['coverage_config'] = test_endpoint(
        "Coverage Portal Config",
        "https://coverage.ddc.teliasonera.net/coverageportal_se/Config/GetConfig"
    )
    
    # Test 10: Try direct HTML page
    results['main_page_html'] = test_endpoint(
        "Main Telia Outage Page",
        "https://www.telia.se/foretag/support/driftinformation",
        params={'category': 'mobila-natet'}
    )
    
    # Summary
    logger.info(f"\n\n{'='*60}")
    logger.info("SUMMARY OF ALL TESTS")
    logger.info(f"{'='*60}")
    
    successful = []
    failed = []
    empty = []
    
    for name, result in results.items():
        if result.get('success'):
            if result.get('type') == 'empty':
                empty.append(name)
            else:
                successful.append(name)
        else:
            failed.append(name)
    
    logger.info(f"\n✓ Successful ({len(successful)}):")
    for name in successful:
        logger.info(f"  - {name}: {results[name].get('type')}")
    
    logger.info(f"\n⚠ Empty responses ({len(empty)}):")
    for name in empty:
        logger.info(f"  - {name}")
    
    logger.info(f"\n✗ Failed ({len(failed)}):")
    for name in failed:
        logger.info(f"  - {name}: {results[name].get('error', 'Unknown error')}")
    
    # Save results
    output_file = "telia_api_debug_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n✓ Full results saved to: {output_file}")


if __name__ == "__main__":
    main()
