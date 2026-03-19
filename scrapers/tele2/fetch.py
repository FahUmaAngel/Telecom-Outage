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
            except:
                pass
                
            input_selector = "input[placeholder='Ange en plats']"
            page.wait_for_selector(input_selector, timeout=10000)
            
            # Probing first 10 addresses for this test/run
            # In production, we can run all 50
            for addr in addresses[:15]: 
                print(f"Probing: {addr['address']}...")
                try:
                    # Clear and fill
                    # Sometimes simple .fill() doesn't trigger autocomplete
                    input_field = page.locator(input_selector)
                    input_field.fill("")
                    input_field.type(addr['address'], delay=50)
                    time.sleep(2)
                    
                    # Select first result from autocomplete
                    # Selector for autocomplete items - usually they appear in a dropdown
                    # Let's try pressing Down and Enter
                    page.keyboard.press("ArrowDown")
                    page.keyboard.press("Enter")
                    time.sleep(3)
                    
                    # After search, check for status text
                    # Tele2 map page shows a legend or a side panel if something is wrong
                    # We look for keywords: 'störning', 'avbrott', 'planerat'
                    page_text = page.inner_text("body").lower()
                    
                    if any(word in page_text for word in ["störning", "avbrott", "fel"]):
                        # If a disturbance is hinted, try to find a more specific element
                        # Usually there is an info card or a list of matches
                        print(f"  [!] Potential outage found for {addr['address']}")
                        
                        # Capture specific elements if possible
                        # This is a bit generic, can be refined once we see real-world outages
                        status_header = "Driftstörning" 
                        # Try to find a panel or bubble text
                        details = page.evaluate("""
                            () => {
                                const elements = Array.from(document.querySelectorAll('div, p, span'));
                                const match = elements.find(el => el.innerText.includes('felet är löst') || el.innerText.includes('pågående störning'));
                                return match ? match.innerText : '';
                            }
                        """)
                        
                        outage = map_tele2_to_outage(addr, status_header, details)
                        if outage:
                            outages.append(outage)
                            print(f"  Captured: {outage['incident_id']}")
                    else:
                        print("  Status: OK")
                        
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
