"""Call Telia GetFaultTimeline endpoint directly with various parameters.

Hypothesis: by setting 'statuses' to include RESOLVED and adding 'dateRange',
we might be able to fetch historical incidents from a stable cookie session.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from urllib.parse import quote
import requests

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
API = "https://coverage.ddc.teliasonera.net/coverageportal_se/NetworkEventsTimeline/NetworkEventsTimeline/GetFaultTimeline"

SERVICES = ["NR700_DATANSA","NR1800_DATANSA","NR2100_DATANSA","NR2600_DATANSA","NR3500_DATANSA",
            "LTE700_DATA","LTE800_DATA","LTE900_DATA","LTE1800_DATA","LTE2100_DATA","LTE2600_DATA",
            "GSM900_VOICE","GSM1800_VOICE"]

# Test points: a few county centers
LOCATIONS = [
    {"name": "Stockholm",  "easting": 18.0686, "northing": 59.3293},
    {"name": "Göteborg",   "easting": 11.9746, "northing": 57.7089},
    {"name": "Malmö",      "easting": 13.0007, "northing": 55.6050},
]

VARIANTS = [
    {"label": "ACTIVE only, no dateRange (baseline)",
     "statuses": ["ACTIVE"], "dateRange": None},
    {"label": "ACTIVE + RESOLVED, no dateRange",
     "statuses": ["ACTIVE", "RESOLVED"], "dateRange": None},
    {"label": "All statuses + date range",
     "statuses": ["ACTIVE", "RESOLVED", "CLOSED"], 
     "dateRange": {"startTime": "2026-04-22", "endTime": "2026-05-16"}},
    {"label": "RESOLVED only + date range",
     "statuses": ["RESOLVED"], 
     "dateRange": {"startTime": "2026-04-22", "endTime": "2026-05-16"}},
    {"label": "Empty statuses + date range",
     "statuses": [], 
     "dateRange": {"startTime": "2026-04-22", "endTime": "2026-05-16"}},
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        print("Initializing session by loading portal...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        # Steal cookies & user-agent for direct request
        cookies = ctx.cookies()
        ua = page.evaluate("navigator.userAgent")
        browser.close()

    sess = requests.Session()
    for c in cookies:
        sess.cookies.set(c['name'], c['value'], domain=c.get('domain'))
    sess.headers.update({
        'User-Agent': ua,
        'Accept': 'application/json',
        'Accept-Language': 'sv-SE,sv;q=0.9',
        'Referer': URL,
    })

    for loc in LOCATIONS:
        print(f"\n\n========== Location: {loc['name']} ==========")
        for var in VARIANTS:
            req = {
                "locations": [{"id": "timeline", "easting": loc['easting'], "northing": loc['northing']}],
                "eventTypes": [],
                "services": SERVICES,
                "statuses": var['statuses'],
                "dateRange": var['dateRange']
            }
            url = f"{API}?request={quote(json.dumps(req, separators=(',', ':')))}"
            try:
                resp = sess.get(url, timeout=30)
                if resp.status_code != 200:
                    print(f"  [{var['label']}] HTTP {resp.status_code}")
                    continue
                data = resp.json()
                ev = data.get('events', {})
                print(f"  [{var['label']}]")
                print(f"    Events={len(ev.get('Events', []))} Neighbour={len(ev.get('NeighbourEvents', []))} Spans={len(ev.get('ImpactTimeSpans', []))}")
                if ev.get('Events'):
                    print(f"    Sample event: {json.dumps(ev['Events'][0], default=str)[:500]}")
                if ev.get('NeighbourEvents'):
                    print(f"    Sample neighbour: {json.dumps(ev['NeighbourEvents'][0], default=str)[:500]}")
            except Exception as e:
                print(f"  [{var['label']}] err: {e}")

if __name__ == "__main__":
    main()