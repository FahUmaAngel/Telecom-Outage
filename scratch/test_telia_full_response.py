"""Examine FULL GetFaultTimeline response to understand fields."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from urllib.parse import unquote

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

def main():
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

        print("Loading...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        # Click somewhere on the map that's likely Stockholm
        # Map bbox was (385, 48, 1535, 819) — Stockholm is east-central Sweden, ~30% from right, 40% from top
        cx, cy = 385 + 1535 * 0.55, 48 + 819 * 0.55
        print(f"Clicking map at ({cx}, {cy})...")
        page.mouse.click(cx, cy)
        page.wait_for_timeout(5000)

        # Switch to historical
        page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=5000)
        page.wait_for_timeout(2000)

        # Click date to open picker
        page.click("input.form-control[placeholder='Välj datum']", timeout=5000)
        page.wait_for_timeout(1500)

        # Pick day 30 in current month (May)
        # Actually try APRIL: prev once
        page.click(".datepicker .datepicker-days th.prev", timeout=3000)
        page.wait_for_timeout(500)
        cur_month = page.evaluate("document.querySelector('.datepicker .datepicker-days .datepicker-switch').textContent")
        print(f"Datepicker showing: {cur_month}")

        # click day 30
        page.locator(".datepicker-days td.day:not(.old):not(.new)").filter(has_text="30").first.click(timeout=3000)
        page.wait_for_timeout(10000)

        print(f"\n=== Got {len(fault_responses)} GetFaultTimeline responses ===\n")
        for i, r in enumerate(fault_responses):
            print(f"--- Response {i} ---")
            print(f"URL: {unquote(r['url'])[:500]}")
            print(f"Body length: {len(r['body'])}")
            try:
                d = json.loads(r['body'])
                print(f"Top keys: {list(d.keys())}")
                if 'events' in d:
                    ev = d['events']
                    print(f"events keys: {list(ev.keys())}")
                    for k, v in ev.items():
                        if isinstance(v, list):
                            print(f"  {k}: list len={len(v)}")
                            if v and len(v) > 0:
                                print(f"    First item: {json.dumps(v[0], default=str)[:600]}")
                        else:
                            print(f"  {k}: {str(v)[:200]}")
                # Print everything else
                for k, v in d.items():
                    if k != 'events':
                        print(f"{k}: {str(v)[:300]}")
            except Exception as e:
                print(f"parse err: {e}")
                print(f"raw: {r['body'][:800]}")
            print()

        browser.close()

if __name__ == "__main__":
    main()