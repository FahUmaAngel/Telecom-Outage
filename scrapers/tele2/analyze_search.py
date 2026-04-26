from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json

def find_target_input(page):
    inputs = page.query_selector_all("input[type='text'], input[type='search']")
    for i in inputs:
        ph = i.get_attribute("placeholder") or ""
        id_attr = i.get_attribute("id") or ""
        if "cookie" in ph.lower() or "cookie" in id_attr.lower():
            continue
        return i
    return None

def interact_with_search(page):
    try:
        page.wait_for_selector("input.location-search, input[placeholder*='Sök'], input[id*='search']", timeout=10000)
        target_input = find_target_input(page)
            
        if target_input:
            target_input.fill("Drottninggatan 1, Stockholm")
            print("Filled address...")
            time.sleep(1)
            target_input.press("ArrowDown")
            time.sleep(1)
            target_input.press("Enter")
            print("Pressed Enter, waiting for responses...")
            time.sleep(10)
        else:
            print("Could not find the correct input box.")
            page.screenshot(path="tele2_search_fail.png")
    except PlaywrightTimeoutError as e:
        print(f"Could not interact with search box (timeout): {e}")
        page.screenshot(path="tele2_search_fail2.png")
    except Exception as e:
        print(f"Could not interact with search box: {e}")
        page.screenshot(path="tele2_search_fail2.png")

def analyze_tele2_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        api_calls = []

        def handle_request(request):
            if 'mim-api' in request.url:
                print(f"\n[MIM API Request] {request.url}")
                print(f"Headers: {request.headers}")
                if request.post_data:
                    print(f"Post Data: {request.post_data}")

        def handle_response(response):
            if 'mim-api' in response.url:
                try:
                    body = response.json()
                    print(f"[MIM API Response] {json.dumps(body)[:1000]}...")
                except Exception as e:
                    print(f"Could not read response: {e}")

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Navigating to Tele2 Outage page...")
        page.goto("https://www.tele2.se/driftstorning-mobilnatet", wait_until="networkidle")
        
        try:
            page.locator("button:has-text('Acceptera alla')").click(timeout=3000)
            print("Accepted cookies.")
        except PlaywrightTimeoutError:
            pass
            
        print("Waiting for search box...")
        interact_with_search(page)
            
        browser.close()

if __name__ == "__main__":
    analyze_tele2_search()
