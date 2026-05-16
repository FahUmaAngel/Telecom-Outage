"""Try clicking on the map to pin a location, then go to historical mode."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"


def main():
    fault_responses = []
    location_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        def on_response(resp):
            if 'GetFaultTimeline' in resp.url:
                try:
                    body = resp.body().decode('utf-8', errors='replace')
                    fault_responses.append({'url': resp.url, 'len': len(body), 'body': body})
                except Exception:
                    pass
            elif 'GetLocationInfo' in resp.url:
                try:
                    body = resp.body().decode('utf-8', errors='replace')[:1000]
                    location_responses.append({'url': resp.url, 'body': body})
                except Exception:
                    pass

        page.on('response', on_response)

        print("1) Loading portal...")
        page.goto(URL, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(4000)

        # Find Google Maps canvas / div
        print("\n2) Finding map area...")
        bbox = page.evaluate("""() => {
            const map = document.querySelector('.gm-style') || document.querySelector('#map') || document.querySelector('[role=\"region\"]');
            if (!map) return null;
            const r = map.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height};
        }""")
        print(f"   map bbox: {bbox}")

        if bbox:
            # Click center of map
            cx, cy = bbox['x'] + bbox['w']/2, bbox['y'] + bbox['h']/2
            print(f"\n3) Clicking map at ({cx}, {cy})...")
            page.mouse.click(cx, cy)
            page.wait_for_timeout(4000)

        # Now switch to historical mode
        print("\n4) Clicking Nätverkshistorik...")
        try:
            page.click("label[for='networkEventsTimelineActivatorRadioHistorical']", timeout=5000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"   err: {e}")

        # Check radio state
        radio_state = page.evaluate("document.getElementById('networkEventsTimelineActivatorRadioHistorical').checked")
        print(f"   Historical radio checked: {radio_state}")

        # Date input state
        di = page.evaluate("""() => {
            const i = document.querySelector(\"input.form-control[placeholder='Välj datum']\");
            return i ? {disabled: i.disabled, value: i.value} : null;
        }""")
        print(f"   Date input state: {di}")

        # Open datepicker and try clicking a date
        print("\n5) Opening datepicker and clicking day 30 (April)...")
        try:
            page.click("input.form-control[placeholder='Välj datum']", timeout=5000)
            page.wait_for_timeout(1500)
            # nav back 1 month (May -> April)
            page.click(".datepicker .datepicker-days th.prev", timeout=3000)
            page.wait_for_timeout(500)
            cur_month = page.evaluate("document.querySelector('.datepicker .datepicker-days .datepicker-switch').textContent")
            print(f"   Datepicker showing: {cur_month}")
            page.locator(".datepicker-days td.day:not(.old):not(.new)").filter(has_text="30").first.click(timeout=3000)
            page.wait_for_timeout(8000)
        except Exception as e:
            print(f"   err: {e}")

        di2 = page.evaluate("""() => {
            const i = document.querySelector(\"input.form-control[placeholder='Välj datum']\");
            return i ? {disabled: i.disabled, value: i.value} : null;
        }""")
        print(f"\n6) Final date input state: {di2}")

        print(f"\n=== GetFaultTimeline responses: {len(fault_responses)} ===")
        for r in fault_responses:
            print(f"  URL: {r['url'][:300]}")
            print(f"  len={r['len']}")
            try:
                d = json.loads(r['body'])
                ev = d.get('events', {})
                print(f"  Events={len(ev.get('Events', []))} Neighbour={len(ev.get('NeighbourEvents', []))} ImpactSpans={len(ev.get('ImpactTimeSpans', []))}")
                if ev.get('Events'):
                    print(f"  Sample event: {json.dumps(ev['Events'][0], default=str)[:800]}")
                if ev.get('NeighbourEvents'):
                    print(f"  Sample neighbour: {json.dumps(ev['NeighbourEvents'][0], default=str)[:800]}")
                if ev.get('ImpactTimeSpans'):
                    print(f"  Sample span: {json.dumps(ev['ImpactTimeSpans'][0], default=str)[:500]}")
            except Exception as e:
                print(f"  parse err: {e}, body={r['body'][:300]}")
            print('---')

        print(f"\n=== GetLocationInfo responses: {len(location_responses)} ===")
        for r in location_responses[:2]:
            print(f"  {r['url'][:200]}")

        browser.close()

if __name__ == "__main__":
    main()