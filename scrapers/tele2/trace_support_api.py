from playwright.sync_api import sync_playwright
import json
import time

def find_support_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        captured_requests = []
        
        def handle_response(response):
            if 'json' in response.headers.get('content-type', '') and response.status == 200:
                captured_requests.append({
                    'url': response.url,
                    'status': response.status,
                    'type': response.request.resource_type
                })

        page.on("response", handle_response)
        
        print("Navigating to Tele2 Support/Outage page...")
        # The subagent visited /support/drift-och-felsok
        page.goto("https://www.tele2.se/support/drift-och-felsok", wait_until="networkidle")
        
        try:
            # Type an address to trigger the status check
            input_selector = "#feasibilityAddress"
            page.wait_for_selector(input_selector, timeout=10000)
            page.fill(input_selector, "Drottninggatan 1, Stockholm")
            time.sleep(2)
            page.keyboard.press("ArrowDown")
            time.sleep(1)
            page.keyboard.press("Enter")
            print("Search triggered, waiting for API calls...")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error during search: {e}")
            
        browser.close()
        
        print("\n=== CAPTURED JSON API CALLS ===")
        for req in captured_requests:
            url = req['url']
            if 'tele2' in url or 'mim' in url:
                print(f"URL: {url}")

if __name__ == "__main__":
    find_support_api()
