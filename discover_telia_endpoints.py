"""
Phase 1: Telia Portal API Endpoint Discovery Script.
Intercepts ALL network requests while simulating the Fel + Plats workflow
to find the exact per-incident drill-down API endpoints.
"""
import logging
import re
import json
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("TeliaEndpointDiscovery")

BASE_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se"
PORTAL_URL = f"{BASE_URL}?appmode=outage"

all_requests = []
all_responses = []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # --- Intercept ALL requests and responses ---
        def on_request(request):
            if "coverageportal" in request.url or "teliasonera" in request.url:
                all_requests.append({
                    "method": request.method,
                    "url": request.url,
                })

        def on_response(response):
            if ("coverageportal" in response.url or "teliasonera" in response.url) and response.status == 200:
                try:
                    body = response.json()
                    all_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "body_preview": str(body)[:200],
                    })
                except:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        # Step 1: Navigate to portal
        logger.info(f"Navigating to {PORTAL_URL}")
        page.goto(PORTAL_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        # Step 2: Click "Fel" tab
        logger.info("Looking for 'Fel' button...")
        try:
            fel_btn = page.locator("text=Fel").first
            if fel_btn.is_visible():
                logger.info("Clicking 'Fel' button")
                fel_btn.click()
                page.wait_for_timeout(3000)
            else:
                logger.warning("'Fel' button not visible")
        except Exception as e:
            logger.error(f"Error clicking Fel: {e}")

        # Step 3: Try to find an incident ID from the initial load, 
        # or look for a visible incident ID on screen
        logger.info("Looking for incident IDs in page text...")
        incident_id = None
        try:
            # Look for incident IDs in the page content (typically Nordic format INCSE... or numeric)
            page_text = page.content()
            # Pattern for Telia incident IDs
            matches = re.findall(r'(INCSE\d{7})', page_text)
            if not matches:
                matches = re.findall(r'"ExternalId"\s*:\s*"([^"]+)"', page_text)
            if not matches:
                # Numeric IDs from Lycamobile-style
                matches = re.findall(r'\b(3\d{7})\b', page_text)
            if matches:
                incident_id = matches[0]
                logger.info(f"Found incident ID: {incident_id}")
            else:
                logger.warning("No incident IDs found in page content")
        except Exception as e:
            logger.error(f"Error finding incident IDs: {e}")

        # Step 4: If we have an incident ID, look for an input field and type it
        if incident_id:
            logger.info(f"Attempting to enter incident ID: {incident_id}")
            try:
                inputs = page.locator("input[type=text], input[type=search], input:not([type])").all()
                logger.info(f"Found {len(inputs)} text inputs on page")
                
                for i, inp in enumerate(inputs):
                    try:
                        if inp.is_visible():
                            placeholder = inp.get_attribute("placeholder") or ""
                            logger.info(f"  Input {i}: placeholder='{placeholder}'")
                    except:
                        pass
                
                # Try the first visible text input
                first_input = page.locator("input[type=text]").first
                if first_input.is_visible():
                    first_input.fill(incident_id)
                    page.wait_for_timeout(1000)
                    first_input.press("Enter")
                    page.wait_for_timeout(3000)
                    logger.info("Entered incident ID and pressed Enter")
            except Exception as e:
                logger.error(f"Error entering incident ID: {e}")

        # Step 5: Click "Plats" tab (location tab)
        logger.info("Looking for 'Plats' button...")
        try:
            plats_btn = page.locator("text=Plats").first
            if plats_btn.is_visible():
                logger.info("Clicking 'Plats' button")
                plats_btn.click()
                page.wait_for_timeout(3000)
            else:
                logger.warning("'Plats' button not visible")
        except Exception as e:
            logger.error(f"Error clicking Plats: {e}")

        # Step 6: Wait for any triggered API calls
        page.wait_for_timeout(3000)

        # Take screenshot for reference
        page.screenshot(path="/tmp/telia_portal_state.png")
        logger.info("Screenshot saved to /tmp/telia_portal_state.png")

        browser.close()

    # --- Print Results ---
    print("\n" + "="*60)
    print("ALL INTERCEPTED REQUESTS TO TELIA PORTAL:")
    print("="*60)
    seen_urls = set()
    for req in all_requests:
        key = f"{req['method']} {req['url']}"
        if key not in seen_urls:
            seen_urls.add(key)
            print(f"  [{req['method']}] {req['url']}")

    print("\n" + "="*60)
    print("RESPONSES WITH JSON DATA:")
    print("="*60)
    for resp in all_responses:
        print(f"\n  URL: {resp['url']}")
        print(f"  Status: {resp['status']}")
        print(f"  Body preview: {resp['body_preview']}")

    print("\n" + "="*60)
    print("FAULT-SPECIFIC ENDPOINTS FOUND:")
    print("="*60)
    fault_endpoints = [r for r in all_requests if "/Fault/" in r['url'] or "/Location/" in r['url'] or "/Plats" in r['url'] or "/Ticket" in r['url']]
    for ep in fault_endpoints:
        print(f"  [{ep['method']}] {ep['url']}")

if __name__ == "__main__":
    main()
