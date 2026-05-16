"""Inspect Telia portal DOM to find correct selectors for historical mode."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
from playwright.sync_api import sync_playwright

URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

def main():
    api_calls = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def on_request(req):
            if any(k in req.url for k in ['AreaTicket', 'Outage', 'History', 'Historik', 'admin']):
                api_calls.append({'method': req.method, 'url': req.url, 'post': req.post_data})

        page.on('request', on_request)

        print(f"Loading {URL}...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        print("\n=== Page Title ===")
        print(page.title())

        print("\n=== Looking for Nätverkshistorik element ===")
        # Try multiple ways
        candidates = [
            ("text", "Nätverkshistorik"),
            ("text", "Historik"),
            ("text", "historik"),
        ]
        for kind, val in candidates:
            try:
                loc = page.get_by_text(val, exact=False)
                cnt = loc.count()
                print(f"  get_by_text('{val}'): count={cnt}")
                for i in range(min(cnt, 5)):
                    el = loc.nth(i)
                    print(f"    [{i}] tag={el.evaluate('el => el.tagName')}, text='{el.inner_text()[:80]}'")
            except Exception as e:
                print(f"  err: {e}")

        print("\n=== Trying to click Nätverkshistorik ===")
        try:
            page.get_by_text("Nätverkshistorik", exact=False).first.click(timeout=5000)
            print("  Clicked!")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"  Click failed: {e}")

        print("\n=== After click - looking for date input ===")
        # Find all visible inputs
        inputs = page.locator("input").all()
        print(f"  Total inputs: {len(inputs)}")
        for i, inp in enumerate(inputs[:20]):
            try:
                visible = inp.is_visible()
                if not visible:
                    continue
                attrs = inp.evaluate("""el => ({
                    type: el.type,
                    placeholder: el.placeholder,
                    name: el.name,
                    id: el.id,
                    cls: el.className,
                    value: el.value,
                    ariaLabel: el.getAttribute('aria-label')
                })""")
                print(f"  [{i}] {attrs}")
            except Exception:
                pass

        print("\n=== API calls during navigation ===")
        for call in api_calls:
            print(f"  {call['method']} {call['url'][:200]}")

        # Try date picker injection
        print("\n=== Looking for buttons / radios near history mode ===")
        try:
            html = page.content()
            # Save HTML for offline inspection
            with open('scratch/telia_portal_inspect.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("  Saved DOM to scratch/telia_portal_inspect.html")

            # Search snippet around 'historik'
            for m in re.finditer(r'historik', html, re.IGNORECASE):
                start = max(0, m.start() - 200)
                end = min(len(html), m.end() + 200)
                snippet = html[start:end].replace('\n', ' ')
                print(f"  ...{snippet}...")
                print("---")
        except Exception as e:
            print(f"  err: {e}")

        browser.close()

if __name__ == "__main__":
    main()