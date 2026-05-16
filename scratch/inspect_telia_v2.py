"""Probe Telia historical: try clicking date input, navigating calendar, watch FaultTimeline."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"


def main():
    captured_events = []
    all_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        def on_request(req):
            url = req.url
            if 'NetworkEvents' in url or 'AreaTicket' in url or 'Fault' in url or 'Timeline' in url:
                all_requests.append((req.method, url))

        def on_response(resp):
            if 'GetFaultTimeline' in resp.url or 'AreaTicket' in resp.url or 'EventTimeline' in resp.url:
                try:
                    body = resp.body().decode('utf-8', errors='replace')
                    captured_events.append({'url': resp.url, 'status': resp.status, 'len': len(body), 'snippet': body[:2000]})
                except Exception as e:
                    captured_events.append({'url': resp.url, 'err': str(e)})

        page.on('request', on_request)
        page.on('response', on_response)

        print("Loading...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        print("\nClicking Nätverkshistorik label...")
        page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=5000)
        page.wait_for_timeout(2000)

        # Click date input to open datepicker
        print("\nClicking date input to open datepicker...")
        page.click("input.form-control[placeholder='Välj datum']")
        page.wait_for_timeout(1500)

        # Try to see datepicker structure
        print("\nLooking for datepicker UI elements (after click)...")
        dp = page.evaluate("""() => {
            const allDivs = Array.from(document.querySelectorAll('div, table, td'));
            const dpCandidates = allDivs.filter(el => {
                const cls = (el.className || '').toString();
                return /datepicker|calendar|picker/i.test(cls);
            });
            return dpCandidates.slice(0, 10).map(el => ({
                tag: el.tagName,
                cls: el.className,
                role: el.getAttribute('role'),
                visible: el.offsetParent !== null,
                html: el.outerHTML.slice(0, 300)
            }));
        }""")
        for d in dp:
            print(f"  {d}")

        # Try clicking a date cell within calendar (try common selectors)
        print("\nLooking for clickable date cells (td.day)...")
        for sel in ['.datepicker td.day', 'td[data-day]', '.day:not(.disabled)', 'td.active']:
            try:
                cnt = page.locator(sel).count()
                print(f"  '{sel}': count={cnt}")
            except Exception:
                pass

        # Try going back to last month
        print("\nTrying to navigate back 1 month via prev button...")
        for sel in ['.datepicker .prev', '.prev', 'th.prev', '.datepicker-switch + .prev', '[class*=prev]']:
            try:
                if page.locator(sel).count() > 0:
                    print(f"  prev btn found at '{sel}'")
                    page.click(sel, timeout=2000)
                    page.wait_for_timeout(1000)
                    break
            except Exception as e:
                pass

        # Click a day cell to set date
        print("\nTrying to click a 'day' cell (e.g. day=10)...")
        try:
            cells = page.locator(".datepicker td.day:not(.old):not(.new)")
            cnt = cells.count()
            print(f"  day cells available: {cnt}")
            if cnt >= 10:
                cells.nth(9).click()  # the 10th day
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"  click day fail: {e}")

        print("\nDate input value now:")
        v = page.evaluate("document.querySelector(\"input.form-control[placeholder='Välj datum']\").value")
        print(f"  {v}")

        print("\n=== ALL Captured Fault/Outage API calls ===")
        for r in captured_events:
            print(r.get('url', '')[:200])
            if 'snippet' in r:
                print(f"  len={r['len']}, snippet={r['snippet'][:400]}")
            print('---')

        print("\n=== ALL Fault/Timeline requests ===")
        for m, u in all_requests:
            print(f"  {m} {u[:200]}")

        browser.close()

if __name__ == "__main__":
    main()