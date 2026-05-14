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
    if not os.path.exists(SEED_FILE):
        print(f"Seed file {SEED_FILE} not found.")
        return []

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        addresses = json.load(f)

    outages = []
    
    with sync_playwright() as p:
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

            for addr in addresses:
                try:
                    print(f"Probing {addr['address']}, {addr['city']}...")
                    # Tele2 map usually requires typing an address
                    input_selector = "input[placeholder*='Gata'], input[id*='search']"
                    if page.locator(input_selector).is_visible():
                        page.locator(input_selector).fill(addr['address'])
                        page.keyboard.press("Enter")
                        time.sleep(2)
                        
                        # Look for status indicators
                        # Note: This part is speculative as we don't have the real DOM structure here
                        # We'll look for generic status indicators
                        status_loc = page.locator(".drift-status-text, .status-header")
                        if status_loc.count() > 0:
                            status_text = status_loc.first.inner_text()
                            desc_loc = page.locator(".drift-detailed-info, .status-description")
                            detailed_text = desc_loc.first.inner_text() if desc_loc.count() > 0 else ""
                            
                            outage = map_tele2_to_outage(addr, status_text, detailed_text)
                            if outage:
                                outages.append(outage)
                except Exception as e:
                    print(f"  Error probing {addr['address']}: {e}")

        except Exception as e:
            print(f"Failed to load map page: {e}")
            
        browser.close()
        
    return outages

if __name__ == "__main__":
    results = scrape_tele2()
    print(f"\nDone. Found {len(results)} Tele2 outages.")
    print(json.dumps(results, indent=2))
