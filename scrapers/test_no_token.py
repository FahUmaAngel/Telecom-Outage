
import requests
import logging

logging.basicConfig(level=logging.INFO)

ticket_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/AreaTicketList"
sweden_bbox = {
    'llx': 10.0,
    'lly': 55.0,
    'urx': 25.0,
    'ury': 70.0
}
params = {
    **sweden_bbox,
    'services': 'LTE700_DATA,LTE800_DATA'
    # No 'ert'
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    # Add Referer as it sometimes helps
    "Referer": "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
}

logging.info("Requesting tickets without token...")
resp = requests.get(ticket_url, params=params, headers=headers)
logging.info(f"Status: {resp.status_code}")
logging.info(f"Content: {resp.text[:500]}")
