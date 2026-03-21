"""
Synchronous comprehensive Tele2 network interceptor.
Designed to fail fast and not hang.
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
            if "json" in ct and ("tele2.se" in url or "mim-api" in url):
                try:
                    data = res.json()
                    all_responses[url] = data
                    print(f"  [CAP] {url}")
                except Exception:
                    pass

        page.on("response", on_response)

        print("1. Loading page...")
        try:
            page.goto(TELE2_URL, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
        except Exception as e:
            print(f"goto: {e}")

        print("2. Trying to accept cookies...")
        try:
            for sel in ["button:has-text('Acceptera alla')", "button:has-text('Acceptera')"]:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click(timeout=3000)
                    print(f"Clicked cookie: {sel}")
                    time.sleep(2)
                    break
        except Exception as e:
            print("Cookie err:", e)

        print("3. Trying to click disturbance list button...")
        try:
            list_selectors = [
                "button:has-text('Pågående störningar')",
                "button:has-text('störning')",
                "button[aria-label*='störning']"
            ]
            clicked = False
            for sel in list_selectors:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click(timeout=3000)
                    print(f"Clicked list: {sel}")
                    clicked = True
                    time.sleep(4)
                    break
            
            if not clicked:
                print("Could not find disturbance list button, clicking random elements...")
                page.mouse.click(100, 100)
                time.sleep(1)
        except Exception as e:
            print("List err:", e)

        time.sleep(2)
        print("Closing browser...")
        browser.close()

    print("\n\n=== RELEVANT OUTPUT ===")
    for url, data in all_responses.items():
        if "mim-api" not in url and "translation" not in url and "kameleoon" not in url and "maintenance" not in url and "whitelisted" not in url and "beacon" not in url:
            print(f"\n{url}")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

if __name__ == "__main__":
    capture()
