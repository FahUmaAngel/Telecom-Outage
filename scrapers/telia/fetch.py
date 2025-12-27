"""
Telia outage data fetcher.
Fetches raw HTML/JSON from Telia's outage information page.
"""
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# NOTE: Telia loads outage data via an iframe that requires JavaScript rendering
# Main page: https://www.telia.se/foretag/support/driftinformation?category=mobila-natet
# Actual data source (iframe): https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage
TELIA_OUTAGE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def fetch_telia_outages(timeout: int = 30) -> Optional[str]:
    """
    Fetch raw HTML content from Telia's outage information page.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if request fails
    """
    try:
        logger.info(f"Fetching Telia outage data from {TELIA_OUTAGE_URL}")
        response = requests.get(
            TELIA_OUTAGE_URL,
            headers=HEADERS,
            timeout=timeout
        )
        response.raise_for_status()
        
        logger.info(f"Successfully fetched Telia data. Status: {response.status_code}, Size: {len(response.text)} bytes")
        return response.text
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching Telia data (timeout={timeout}s)")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Telia data: {e}")
        return None


def fetch_telia_api(api_url: str, timeout: int = 30) -> Optional[dict]:
    """
    Fetch JSON data from Telia API endpoint (if available).
    
    Args:
        api_url: API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        JSON response as dict, or None if request fails
    """
    try:
        logger.info(f"Fetching Telia API data from {api_url}")
        response = requests.get(
            api_url,
            headers=HEADERS,
            timeout=timeout
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched Telia API data")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Telia API data: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error parsing JSON from Telia API: {e}")
        return None


if __name__ == "__main__":
    # Test the fetcher
    logging.basicConfig(level=logging.INFO)
    
    html = fetch_telia_outages()
    if html:
        print(f"✓ Successfully fetched {len(html)} bytes from Telia")
        print(f"First 500 characters:\n{html[:500]}")
    else:
        print("✗ Failed to fetch data from Telia")
