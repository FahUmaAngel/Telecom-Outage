import asyncio
from playwright.async_api import async_playwright
import sqlite3
import re
import sys
import os

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

async def run():
    print("Starting Playwright to fetch accurate Telia regions...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept API calls to catch AreaTicketList or RegionFaultList
        incident_regions = {}
        
        async def handle_response(response):
            if "coverageportal_se/Fault/AreaTicketList" in response.url or "coverageportal_se/Fault/AdminAreaList" in response.url:
                try:
                    data = await response.json()
                    # If this is AreaTicketList, it returns a list of tickets
                    if isinstance(data, list) and len(data) > 0 and 'Id' in data[0]:
                        # The URL usually has bounding box info, but let's let the UI do its thing
                        pass
                except:
                    pass
        
        page.on("response", handle_response)
        
        await page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage")
        await page.wait_for_timeout(5000)
        
        # Click "Fel" (Faults)
        fel_buttons = await page.locator("text=Fel").all()
        for btn in fel_buttons:
            try:
                if await btn.is_visible():
                    await btn.click()
                    print("Clicked 'Fel' button")
                    break
            except:
                pass
                
        await page.wait_for_timeout(3000)
        
        # Now find all "Visa område" buttons
        buttons = await page.locator("button:has-text('Visa område')").all()
        print(f"Found {len(buttons)} regional buttons")
        
        for i in range(len(buttons)):
            try:
                # Re-locate buttons to avoid stale element
                btns = await page.locator("button:has-text('Visa område')").all()
                if i >= len(btns): break
                btn = btns[i]
                
                # Get region name from the row
                row = await btn.evaluate_handle("el => el.closest('tr')")
                text_content = await row.evaluate("el => el.innerText")
                
                # Clean up region name (usually the first text before buttons)
                region_name = text_content.replace('Visa område', '').split('\t')[0].strip()
                if not region_name:
                    cells = await row.query_selector_all("td")
                    if cells:
                        region_name = await cells[0].inner_text()
                
                region_name = region_name.strip()
                print(f"Expanding: {region_name}")
                
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(2000)
                
                # Extract incidents shown right below it in the table
                # The expanded table usually has rows with INCSE IDs
                doc_html = await page.content()
                
                # Find all incidents that are currently visible
                # We can just look for INCSE IDs in the newly loaded table
                # A robust way is to find the table that just became visible.
                
                # Using regex on the whole HTML is risky if previous tables stay in DOM.
                # Let's find the specific accordion body that is 'in' or 'collapse in' or visible
                visible_tables = await page.locator("table:visible").all()
                for table in visible_tables:
                    html = await table.inner_html()
                    ids = re.findall(r'INCSE\d+', html)
                    for inc_id in set(ids):
                        if inc_id not in incident_regions:
                            incident_regions[inc_id] = region_name
                            
            except Exception as e:
                print(f"Error on button {i}: {e}")
                
        print("\nMapping found:")
        for inc_id, reg in incident_regions.items():
            print(f"{inc_id} -> {reg}")
            
        await browser.close()
        
        if not incident_regions:
            print("No incidents mapped!")
            return
            
        # Update DB
        conn = sqlite3.connect('telecom_outage.db')
        cursor = conn.cursor()
        updated = 0
        for inc_id, region in incident_regions.items():
            coords = get_county_coordinates(region, jitter=True)
            if coords:
                cursor.execute("""
                    UPDATE outages
                    SET location = ?, latitude = ?, longitude = ?
                    WHERE incident_id = ? AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
                """, (region, coords[0], coords[1], inc_id))
            else:
                cursor.execute("""
                    UPDATE outages
                    SET location = ?
                    WHERE incident_id = ? AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
                """, (region, inc_id))
            updated += cursor.rowcount
            
        conn.commit()
        conn.close()
        print(f"\nSuccessfully updated {updated} database records with exact regions.")

if __name__ == "__main__":
    asyncio.run(run())
