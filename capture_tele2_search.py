"""
Intercept Tele2 API by searching an address.
"""
import json
import time
from playwright.sync_api import sync_playwright

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

def capture():
    all_responses = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="sv-SE"
        )
        page = context.new_page()

        def on_response(res):
            url = res.url
            ct = res.headers.get("content-type", "")
            if "json" in ct and ("tele2" in url or "mim" in url):
                try:
                    data = res.json()
                    all_responses[url] = data
                except Exception:
                    pass

        page.on("response", on_response)

        print("Navigating...")
        try:
            page.goto(TELE2_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
        except Exception as e:
            print(f"goto: {e}")

        # Accept cookies
        try:
            for sel in ["button:has-text('Acceptera alla')", "button:has-text('Acceptera')"]:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click()
                    time.sleep(2)
                    break
        except Exception:
            pass

        print("Searching for address...")
        try:
            input_sel = "input[placeholder*='Sök'], input[placeholder*='sök'], input[type='search'], input[placeholder*='plats']"
            page.wait_for_selector(input_sel, timeout=5000)
            page.fill(input_sel, "Stockholm")
            time.sleep(2)
            # Press enter or click first dropdown result
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            print("Pressed Enter on search.")
            time.sleep(5)
            
            # Click something on the map just in case
            page.mouse.click(500, 500)
            time.sleep(3)
        except Exception as e:
            print("Search err:", e)

        browser.close()

    print("\n\n=== RELEVANT INTERCEPTED URLS ===")
    for url, data in all_responses.items():
        if "mim-api" in url or "ticket" in url.lower() or "fault" in url.lower() or "coverage" in url.lower() or "search" in url.lower():
            print(f"\n{url}")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:300])

if __name__ == "__main__":
    capture()
