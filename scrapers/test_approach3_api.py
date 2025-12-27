"""
Approach 3: Find and test API endpoints
Analyze HTML and JavaScript to find API calls
"""
import re
import json
import requests
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


def find_api_endpoints_in_html(html_content: str) -> list:
    """
    Search for API endpoint patterns in HTML and JavaScript.
    
    Returns:
        List of potential API endpoints
    """
    endpoints = []
    
    # Common API patterns
    patterns = [
        r'https?://[^\s"\'<>]+/api/[^\s"\'<>]+',
        r'/api/[^\s"\'<>]+',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.get\(["\']([^"\']+)["\']',
        r'"url":\s*"([^"]+)"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        endpoints.extend(matches)
    
    # Remove duplicates and filter
    endpoints = list(set(endpoints))
    endpoints = [e for e in endpoints if 'api' in e.lower() or 'data' in e.lower()]
    
    return endpoints


def test_common_api_patterns() -> list:
    """
    Test common API endpoint patterns for Telia.
    
    Returns:
        List of working endpoints with their responses
    """
    base_url = "https://www.telia.se"
    
    # Common patterns to try
    test_endpoints = [
        "/api/outages",
        "/api/outages/current",
        "/api/outages/mobile",
        "/api/drift",
        "/api/driftinformation",
        "/api/network/status",
        "/api/network/outages",
        "/foretag/api/outages",
        "/foretag/api/driftinformation",
        "/_next/data/*/foretag/support/driftinformation.json",
    ]
    
    working_endpoints = []
    
    for endpoint in test_endpoints:
        try:
            # Handle Next.js data pattern
            if '*' in endpoint:
                # Try to find build ID from HTML
                continue
            
            url = base_url + endpoint
            logger.info(f"Testing: {url}")
            
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ SUCCESS: {url} (Status: {response.status_code})")
                working_endpoints.append({
                    'url': url,
                    'status': response.status_code,
                    'content_type': response.headers.get('Content-Type', ''),
                    'size': len(response.content),
                    'data': response.text[:500]  # First 500 chars
                })
            elif response.status_code == 404:
                logger.debug(f"✗ Not found: {url}")
            else:
                logger.info(f"? Status {response.status_code}: {url}")
                
        except Exception as e:
            logger.debug(f"Error testing {endpoint}: {e}")
    
    return working_endpoints


def analyze_nextjs_data_endpoint(html_content: str) -> str:
    """
    Find Next.js data endpoint from HTML.
    Next.js uses pattern: /_next/data/{buildId}/{page}.json
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if script_tag:
            data = json.loads(script_tag.string)
            build_id = data.get('buildId', '')
            page = data.get('page', '')
            
            if build_id and page:
                # Remove leading slash from page
                page_path = page.lstrip('/')
                endpoint = f"/_next/data/{build_id}/{page_path}.json"
                logger.info(f"Found Next.js data endpoint: {endpoint}")
                return endpoint
    except Exception as e:
        logger.error(f"Error analyzing Next.js endpoint: {e}")
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("APPROACH 3: Finding API Endpoints")
    print("=" * 60)
    
    # Load saved HTML
    with open('telia_raw_output.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Step 1: Find endpoints in HTML/JS
    print("\n[1/3] Searching for API endpoints in HTML...")
    found_endpoints = find_api_endpoints_in_html(html)
    
    if found_endpoints:
        print(f"✓ Found {len(found_endpoints)} potential endpoints:")
        for ep in found_endpoints[:10]:
            print(f"  - {ep}")
    else:
        print("✗ No obvious API endpoints found in HTML")
    
    # Step 2: Try Next.js data endpoint
    print("\n[2/3] Analyzing Next.js data endpoint...")
    nextjs_endpoint = analyze_nextjs_data_endpoint(html)
    
    if nextjs_endpoint:
        print(f"✓ Next.js endpoint: {nextjs_endpoint}")
        try:
            url = f"https://www.telia.se{nextjs_endpoint}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Save for inspection
                with open('telia_nextjs_api.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved response to: telia_nextjs_api.json")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Step 3: Test common patterns
    print("\n[3/3] Testing common API patterns...")
    working = test_common_api_patterns()
    
    if working:
        print(f"\n✓ Found {len(working)} working endpoints:")
        for ep in working:
            print(f"\n  URL: {ep['url']}")
            print(f"  Type: {ep['content_type']}")
            print(f"  Size: {ep['size']} bytes")
            
            # Save responses
            filename = ep['url'].split('/')[-1] or 'response'
            with open(f"api_response_{filename}.txt", 'w', encoding='utf-8') as f:
                f.write(ep['data'])
    else:
        print("\n✗ No working API endpoints found")
        print("\nThis suggests Telia might:")
        print("  1. Use a different domain for API calls")
        print("  2. Require authentication or specific headers")
        print("  3. Load data through WebSocket or other methods")
    
    print("\n" + "=" * 60)
    print("RESULT: Approach 3 - " + ("SUCCESS" if working or nextjs_endpoint else "PARTIAL"))
    print("=" * 60)
