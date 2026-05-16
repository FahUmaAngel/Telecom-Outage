"""Test scraping FaultTimeline at a real county center (Stockholm)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from scrapers.common.geocoding import get_county_coordinates

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

COUNTIES_TO_TEST = ["Stockholms län", "Skåne län", "Västra Götalands län"]
# Use 2026-05-10 (mid-gap)
# Datepicker shows current month "maj 2026", so 0 prev clicks needed.
TARGET_MONTH_OFFSET = 0
TARGET_DAY = 10


def wait_for_responses(handler_state, timeout_s=10):
    import time as t
    start = t.time()
    while t.time() - start < timeout_s:
        if handler_state['fault_count'] > 0:
            t.sleep(2)
            return
        t.sleep(0.5)


def main():
    # Map -- we need to convert county coordinates (lat,lon) into approximate screen pixels.
    # The Google Map is centered initially on Sweden; we will use the search box instead.
    fault_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        def on_response(resp):
            if 'GetFaultTimeline' in resp.url:
                try:
                    body = resp.body().decode('utf-8', errors='replace')
                    fault_responses.append({'url': resp.url, 'body': body})
                except Exception:
                    pass

        page.on('response', on_response)

        print("Loading portal...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        for county in COUNTIES_TO_TEST:
            print(f"\n\n========== {county} ==========")
            coords = get_county_coordinates(county, jitter=False)
            if not coords:
                print(f"  No coordinates known.")
                continue
            lat, lon = coords
            print(f"  Center: lat={lat}, lon={lon}")

            # Use Google Places search to pin location
            # First clear search box if any
            try:
                search = page.locator("input.pac-target-input").first
                if search.is_visible():
                    search.fill("")
                    page.wait_for_timeout(500)
                    search.fill(county)
                    page.wait_for_timeout(2500)
                    pac_items = page.locator(".pac-item")
                    if pac_items.count() > 0:
                        pac_items.first.click(timeout=3000)
                        print(f"  selected pac-item")
                        page.wait_for_timeout(4000)
                    else:
                        search.press("Enter")
                        page.wait_for_timeout(4000)
                else:
                    print("  search box not visible")
            except Exception as e:
                print(f"  search err: {e}")

            # Switch to historical
            try:
                page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=3000)
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"  hist click err: {e}")

            # Open datepicker, click day
            initial_count = len(fault_responses)
            try:
                page.click("input.form-control[placeholder='Välj datum']", timeout=3000)
                page.wait_for_timeout(1000)
                for _ in range(TARGET_MONTH_OFFSET):
                    page.click(".datepicker .datepicker-days th.prev", timeout=2000)
                    page.wait_for_timeout(500)
                cur_month = page.evaluate("document.querySelector('.datepicker .datepicker-days .datepicker-switch').textContent")
                print(f"  Datepicker month: {cur_month}")
                page.locator(".datepicker-days td.day:not(.old):not(.new)").filter(has_text=str(TARGET_DAY)).first.click(timeout=3000)
                page.wait_for_timeout(8000)
            except Exception as e:
                print(f"  date click err: {e}")

            # Report what we caught
            new_responses = fault_responses[initial_count:]
            print(f"  Got {len(new_responses)} new FaultTimeline responses")
            for r in new_responses:
                try:
                    d = json.loads(r['body'])
                    ev = d.get('events', {})
                    events_count = len(ev.get('Events', []))
                    neighbour_count = len(ev.get('NeighbourEvents', []))
                    spans_count = len(ev.get('ImpactTimeSpans', []))
                    print(f"  Events={events_count} Neighbour={neighbour_count} Spans={spans_count}")
                    if events_count > 0:
                        ev0 = ev['Events'][0]
                        print(f"  Sample Event keys: {list(ev0.keys())}")
                        print(f"  Sample Event: {json.dumps(ev0, default=str)[:600]}")
                    if neighbour_count > 0:
                        n0 = ev['NeighbourEvents'][0]
                        print(f"  Sample Neighbour keys: {list(n0.keys())}")
                        print(f"  Sample Neighbour: {json.dumps(n0, default=str)[:600]}")
                except Exception as e:
                    print(f"  parse err: {e}")

        browser.close()

if __name__ == "__main__":
    main()