
import requests
import logging
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TestAPI")

from urllib.parse import unquote

def test_api(base_url, operator_name, token_param="ert"):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    })
    
    logger.info(f"[{operator_name}] Fetching token from {base_url}")
    resp = session.get(f"{base_url}?appmode=outage", timeout=10)
    
    logger.info(f"[{operator_name}] Cookies after first request: {session.cookies.get_dict()}")
    
    token = None
    match = re.search(r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', resp.text)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\']\s+id=["\']csrft["\']', resp.text)
    if match:
        token = unquote(match.group(1))
        logger.info(f"[{operator_name}] Found token (unquoted): {token[:20]}...")
    
    if not token:
        logger.error(f"[{operator_name}] Token not found")
        # Proceed anyway to test cookie-only
    
    # Try AreaTicketList with known-good params from trace
    url = f"{base_url}/Fault/AreaTicketList"
    
    # Format 1: Exact params from trace (Telia example)
    params1 = {
        'llx': -2.71, 'lly': 58.05,
        'urx': 30.71, 'ury': 66.38,
        'services': 'NR700_DATANSA,NR1800_DATANSA,NR3500_DATANSA,LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,GSM900_VOICE,GSM1800_VOICE',
        token_param: token if token else ""
    }
    
    # Format 2: Raw token (double encoded in URL) + same params
    params2 = params1.copy()
    if match:
        params2[token_param] = match.group(1)

    # Format 3: No token (cookie only test)
    params3 = params1.copy()
    if token_param in params3: del params3[token_param]

    for i, p in enumerate([params1, params2, params3], 1):
        logger.info(f"[{operator_name}] Testing Format {i} with params {list(p.keys())}")
        try:
            r = session.get(url, params=p, timeout=10)
            logger.info(f"[{operator_name}] Format {i} Result: {r.status_code}, Length: {len(r.text)}")
            if r.status_code == 200 and r.text.strip():
                try:
                    data = r.json()
                    logger.info(f"[{operator_name}] Format {i} success! Found {len(data)} items")
                    print(f"--- {operator_name} Format {i} Samples ---")
                    print(r.text[:500])
                    break
                except:
                    logger.error(f"[{operator_name}] Format {i} returned non-JSON: {r.text[:100]}")
            elif r.status_code == 500:
                print(f"--- {operator_name} Format {i} 500 Error Body ---")
                print(r.text)
            else:
                logger.info(f"[{operator_name}] Format {i} empty or error")
        except Exception as e:
            logger.error(f"[{operator_name}] Format {i} exception: {e}")

if __name__ == "__main__":
    test_api("https://coverage.ddc.teliasonera.net/coverageportal_se", "Telia", "ert")
    test_api("https://mboss.telenor.se/coverageportal", "Lycamobile", "rt")
