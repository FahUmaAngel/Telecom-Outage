"""Walk through Telia historical flow and log all API calls."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
import time

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
TARGET_DATE = "2026-05-10"  # try a recent date in the gap

def main():
    api_calls = []
    responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        def on_request(req):
            api_calls.append((time.strftime('%H:%M:%S'), req.method, req.url))

        def on_response(resp):
            if any(k in resp.url for k in ['AreaTicket', 'Outage', 'History', 'Ticket', 'admin', 'Event', 'Network']):
                size = 0
                snippet = ''
                try:
                    body = resp.body()
                    size = len(body)
                    snippet = body[:300].decode('utf-8', errors='replace')
                except Exception:
                    pass
                responses.append((resp.status, resp.url, size, snippet))

        page.on('request', on_request)
        page.on('response', on_response)

        print(f"1) Loading {URL}")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        print("\n2) Clicking Nätverkshistorik radio (by id)...")
        try:
            # Click the parent label, not the disabled input itself
            page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=5000)
            print("   clicked label")
        except Exception as e:
            print(f"   label fail: {e}")
            try:
                page.evaluate("document.getElementById('networkEventsTimelineActivatorRadioHistorical').click()")
                print("   clicked via JS")
            except Exception as e2:
                print(f"   JS fail: {e2}")
        page.wait_for_timeout(2000)

        print("\n3) Inspecting date input state after radio click...")
        di_info = page.evaluate("""() => {
            const inputs = Array.from(document.querySelectorAll('input.form-control'))
              .filter(i => i.placeholder && i.placeholder.toLowerCase().includes('datum'));
            return inputs.map(i => ({
              disabled: i.disabled,
              value: i.value,
              placeholder: i.placeholder,
              parentCls: i.parentElement && i.parentElement.className
            }));
        }""")
        print(f"   date inputs: {di_info}")

        print(f"\n4) Filling date with {TARGET_DATE} ...")
        try:
            page.fill("input.form-control[placeholder*='datum' i]", TARGET_DATE, timeout=5000)
            print("   filled")
        except Exception as e:
            print(f"   fill fail: {e}")
        page.wait_for_timeout(1000)

        # Press Enter
        print("\n5) Pressing Enter on date input...")
        try:
            page.press("input.form-control[placeholder*='datum' i]", "Enter")
        except Exception as e:
            print(f"   Enter fail: {e}")
        page.wait_for_timeout(5000)

        # Try clicking the calendar icon if there's one (some datepickers need apply button)
        print("\n6) Looking for date confirm buttons...")
        for sel in ["button:has-text('Sök')", "button:has-text('Ok')", "button:has-text('Apply')", ".btn-primary", "button.search"]:
            try:
                cnt = page.locator(sel).count()
                print(f"   {sel}: count={cnt}")
            except Exception:
                pass

        # Dump the value of the date input now
        print("\n7) Final date input state:")
        final_state = page.evaluate("""() => {
            const i = document.querySelector(\"input.form-control[placeholder*='datum' i], input.form-control[placeholder*='Datum' i]\");
            return i ? {value: i.value, disabled: i.disabled} : null;
        }""")
        print(f"   {final_state}")

        page.wait_for_timeout(3000)

        print("\n=== Recent API requests during flow ===")
        for ts, m, url in api_calls[-60:]:
            print(f"  {ts} {m} {url[:200]}")

        print("\n=== Responses to known endpoints ===")
        for status, url, size, snippet in responses:
            print(f"  [{status}] size={size} {url[:200]}")
            print(f"    body[:300]={snippet[:300]}")
            print('---')

        browser.close()

if __name__ == "__main__":
    main()