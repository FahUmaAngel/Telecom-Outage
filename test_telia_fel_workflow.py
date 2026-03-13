"""
Phase 2: Intercept the specific API calls when filling in the Fel form
and switching to Plats tab. This simulates the exact UI workflow the user described.
"""
import logging
import re
import json
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("TeliaFelWorkflow")

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
PORTAL_URL = f"{BASE_URL}?appmode=outage"

# Sample Telia incident IDs from our database
TEST_INCIDENT_IDS = ["INCSE0425201", "INCSE0408937", "INCSE0382662"]

def main():
    captured = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def on_response(response):
            if ("coverageportal" in response.url or "teliasonera" in response.url) and response.status == 200:
                try:
                    body = response.json()
                    if body and body != {} and body is not None:
                        # Store anything non-empty
                        captured.append({"url": response.url, "body": body})
                except:
                    pass

        page.on("response", on_response)

        logger.info("Step 1: Loading portal...")
        page.goto(PORTAL_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Step 2: Click Fel
        logger.info("Step 2: Clicking 'Fel'...")
        try:
            fel = page.locator("button:has-text('Fel'), a:has-text('Fel'), li:has-text('Fel'), text=Fel").first
            fel.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            logger.warning(f"Fel button: {e}")
        
        # Print all visible text to understand structure
        logger.info("Getting page text...")
        try:
            sidebar_text = page.locator("aside, .sidebar, #sidebar, nav").inner_text()
            print(f"\nSIDEBAR TEXT:\n{sidebar_text[:500]}\n")
        except:
            pass
        
        # Print all buttons
        logger.info("Finding all buttons/links...")
        try:
            all_els = page.locator("button, a, li[role='button']").all()
            for el in all_els[:20]:
                try:
                    txt = el.inner_text().strip()
                    if txt:
                        print(f"  [{el.evaluate('e => e.tagName')}] {txt[:50]}")
                except:
                    pass
        except:
            pass
        
        # Screenshot state
        page.screenshot(path="/tmp/telia_fel_state.png")
        
        # Try entering incident in Fel input
        test_id = TEST_INCIDENT_IDS[0]
        logger.info(f"Step 3: Looking for input to enter {test_id}...")
        try:
            inputs = page.locator("input").all()
            for i, inp in enumerate(inputs):
                try:
                    placeholder = inp.get_attribute("placeholder") or ""
                    visible = inp.is_visible()
                    print(f"  Input {i}: type={inp.get_attribute('type')}, placeholder='{placeholder}', visible={visible}")
                except:
                    pass
        except Exception as e:
            logger.error(f"Error listing inputs: {e}")
        
        # Try the actual search
        logger.info(f"Step 4: Entering {test_id} in a search field...")
        try:
            # Try multiple selector approaches
            for selector in [
                "input[placeholder*='inc' i]",
                "input[placeholder*='ärende' i]",
                "input[placeholder*='search' i]",
                "input[placeholder*='ärend' i]",
                "input[type='text']:visible",
                "input:visible"
            ]:
                try:
                    inp = page.locator(selector).first
                    if inp.is_visible():
                        logger.info(f"  Found input with selector: {selector}")
                        inp.fill(test_id)
                        page.wait_for_timeout(1000)
                        inp.press("Enter")
                        page.wait_for_timeout(3000)
                        break
                except:
                    continue
        except Exception as e:
            logger.error(f"Error entering incident ID: {e}")
        
        # Screenshot after entering incident ID
        page.screenshot(path="/tmp/telia_after_incident.png")
        
        # Step 5: Click Plats
        logger.info("Step 5: Clicking 'Plats'...")
        try:
            plats = page.locator("button:has-text('Plats'), a:has-text('Plats'), text=Plats").first
            plats.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            logger.warning(f"Plats button: {e}")
        
        page.screenshot(path="/tmp/telia_plats_state.png")
        page.wait_for_timeout(3000)
        browser.close()
    
    print("\n" + "="*60)
    print(f"Captured {len(captured)} JSON responses")
    print("="*60)
    for item in captured:
        # Only show Fault related
        if any(k in item['url'] for k in ['/Fault/', '/Location/', '/Outage/', '/Ticket', '/Plats']):
            print(f"\nURL: {item['url']}")
            print(f"Body: {json.dumps(item['body'])[:300]}")

if __name__ == "__main__":
    main()
