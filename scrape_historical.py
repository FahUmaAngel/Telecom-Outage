import json
import time
import os
from playwright.sync_api import sync_playwright

def scrape():
    target_ids = [
        "INCSE0504255", "INCSE0500172", "INCSE0508251", "INCSE0504462",
        "INCSE0505843", "INCSE0499021", "INCSE0506219", "INCSE0507801",
        "INCSE0498666", "INCSE0505464", "INCSE0505881", "INCSE0505885",
        "INCSE0505922", "INCSE0506172", "INCSE0502696", "INCSE0502697",
        "INCSE0502694", "INCSE0508167", "INCSE0508249", "INCSE0508259",
        "INCSE0508273", "INCSE0505543", "INCSE0507001", "INCSE0497828",
        "INCSE0505870", "INCSE0505021", "INCSE0497843", "INCSE0508289",
        "INCSE0506784", "INCSE0502566"
    ]
    target_ids = list(set(target_ids))

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # Intercept and store all ticket list responses
        def handle_response(response):
            if "GetAreaTicketList" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        for ticket in data:
                            ext_id = ticket.get("ExternalId")
                            if ext_id in target_ids:
                                results[ext_id] = ticket
                                print(f"Captured ticket via API: {ext_id}")
                except Exception:
                    pass

        page.on("response", handle_response)

        print("Navigating to Telia portal...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)

        # Click Fel
        try:
            page.locator("text=Fel").first.click(timeout=5000)
            time.sleep(1)
        except:
            print("Could not click Fel tab")

        # Select historical
        try:
            page.locator("text=Nätverkshistorik").click(timeout=5000)
            time.sleep(2)
        except:
            print("Could not click Nätverkshistorik")

        # Try searching for each ID directly if possible
        # Or iterate through regions to trigger API calls
        print("Iterating through regions to trigger API calls...")
        regions = page.locator("text=Visa område")
        count = regions.count()
        print(f"Found {count} regions.")

        for i in range(count):
            try:
                region = regions.nth(i)
                region_name = region.evaluate("el => el.parentElement.parentElement.innerText").split('\n')[0]
                print(f"Checking region: {region_name}")
                region.click()
                time.sleep(1.5)
                # After clicking, the API for that region should be triggered
                # Go back to the list
                page.locator("text=Fel").first.click()
                time.sleep(1)
            except Exception as e:
                print(f"Error checking region index {i}: {e}")

        # If any are still missing, try searching specifically for them
        missing_ids = [tid for tid in target_ids if tid not in results]
        if missing_ids:
            print(f"Still missing {len(missing_ids)} IDs. Trying direct search...")
            search_input = page.locator("input[placeholder='Ange ett felnummer']")
            for tid in missing_ids:
                try:
                    print(f"Searching for {tid}...")
                    search_input.fill(tid)
                    page.keyboard.press("Enter")
                    time.sleep(2)
                    # Check if any new tickets were captured via handle_response
                except:
                    pass

        browser.close()

    print(f"Scraping complete. Found {len(results)} out of {len(target_ids)} targets.")
    with open("recovered_historical_incidents.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape()
