"""Test full Telia historical flow: search location, set date, intercept FaultTimeline."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

# Test target: simulate looking at Stockholm in late April 2026
TEST_CITY = "Stockholm"
TARGET_DATE_DAY = 30  # 30 April
TARGET_MONTH_OFFSET = 0  # 0 = current month (May 2026), 1 = prev (April), 2 = March...


def main():
    fault_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        def on_response(resp):
            if 'GetFaultTimeline' in resp.url:
                try:
                    body = resp.body().decode('utf-8', errors='replace')
                    fault_responses.append({'url': resp.url, 'len': len(body), 'body': body[:5000]})
                except Exception as e:
                    pass

        page.on('response', on_response)

        print("1) Loading portal...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        print(f"2) Searching for location '{TEST_CITY}'...")
        # The portal has a Google Places search box at top
        # Find search input by placeholder or aria
        search_candidates = [
            "input[placeholder*='ök' i]",
            "input[placeholder*='address' i]",
            "input[type='text'][autocomplete='off']",
            "input.pac-target-input",
        ]
        for sel in search_candidates:
            try:
                cnt = page.locator(sel).count()
                if cnt > 0:
                    inp = page.locator(sel).first
                    if inp.is_visible():
                        print(f"   using {sel}")
                        inp.click()
                        inp.fill(TEST_CITY)
                        page.wait_for_timeout(2000)
                        # Wait for autocomplete
                        try:
                            page.locator(".pac-item").first.click(timeout=5000)
                            print("   selected first pac-item")
                        except Exception:
                            inp.press("Enter")
                            print("   pressed Enter")
                        page.wait_for_timeout(5000)
                        break
            except Exception as e:
                print(f"   {sel} err: {e}")

        print("\n3) Clicking Nätverkshistorik label...")
        try:
            page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=5000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"   err: {e}")

        print("\n4) Clicking date input to open datepicker...")
        try:
            page.click("input.form-control[placeholder='Välj datum']", timeout=5000)
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"   err: {e}")

        print(f"\n5) Navigating back {TARGET_MONTH_OFFSET} month(s) via .prev...")
        for _ in range(TARGET_MONTH_OFFSET):
            try:
                page.click(".datepicker .datepicker-days th.prev", timeout=3000)
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"   prev err: {e}")
                break

        # Show current displayed month
        cur_month = page.evaluate("document.querySelector('.datepicker .datepicker-days .datepicker-switch') ? document.querySelector('.datepicker .datepicker-days .datepicker-switch').textContent : 'N/A'")
        print(f"   Datepicker showing month: {cur_month}")

        print(f"\n6) Clicking day {TARGET_DATE_DAY}...")
        try:
            # locate td.day with text == target day, not class 'old' or 'new'
            day_cell = page.locator(f".datepicker-days td.day:not(.old):not(.new)").filter(has_text=str(TARGET_DATE_DAY)).first
            day_cell.click(timeout=3000)
            page.wait_for_timeout(8000)  # wait for FaultTimeline
        except Exception as e:
            print(f"   click day err: {e}")

        print("\n7) Date input value:")
        v = page.evaluate("document.querySelector(\"input.form-control[placeholder='Välj datum']\").value")
        print(f"   {v}")

        # Show fault responses
        print(f"\n=== Captured GetFaultTimeline responses: {len(fault_responses)} ===")
        for r in fault_responses:
            print(f"  URL: {r['url'][:300]}")
            print(f"  len={r['len']}")
            try:
                data = json.loads(r['body']) if r['len'] > 0 else None
                if data:
                    events = data.get('events', {})
                    print(f"  Events count: {len(events.get('Events', []))}")
                    print(f"  NeighbourEvents count: {len(events.get('NeighbourEvents', []))}")
                    print(f"  ImpactTimeSpans count: {len(events.get('ImpactTimeSpans', []))}")
                    if events.get('Events'):
                        print(f"  Sample event keys: {list(events['Events'][0].keys()) if events['Events'] else 'none'}")
                        print(f"  Sample event: {json.dumps(events['Events'][0], default=str)[:500]}")
            except Exception as e:
                print(f"  parse err: {e}")
                print(f"  raw: {r['body'][:500]}")
            print('---')

        browser.close()

if __name__ == "__main__":
    main()