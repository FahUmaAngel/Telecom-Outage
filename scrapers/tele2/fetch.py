import json
import time
import os
from playwright.sync_api import sync_playwright
try:
    from scrapers.tele2.mapper import map_tele2_to_outage
except ImportError:
    from mapper import map_tele2_to_outage

# Load seed addresses
SEED_FILE = os.path.join(os.path.dirname(__file__), "tele2_seed_addresses.json")

def scrape_tele2():
    outages = []
    
    with sync_playwright() as p:
        # Using a fixed browser context to handle sessions
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to Tele2 Outage Map...")
        try:
            page.goto("https://www.tele2.se/driftstorning-mobilnatet", wait_until="networkidle", timeout=60000)
            
            # Accept cookies
            try:
                page.locator("button:has-text('Acceptera alla')").click(timeout=5000)
                print("Cookies accepted.")
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to load map page: {e}")
            browser.close()
            return []
            
        browser.close()
        
    return outages

if __name__ == "__main__":
    results = scrape_tele2()
    print(f"\nDone. Found {len(results)} Tele2 outages.")
    print(json.dumps(results, indent=2))
