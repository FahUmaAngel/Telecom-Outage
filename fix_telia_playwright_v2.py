import asyncio
from playwright.async_api import async_playwright
import sqlite3
import re
import sys
import os

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

async def run():
    print("Starting Playwright to parse regions and incidents...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        await page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Click "Fel" (Faults) to ensure the table loads
        fel_buttons = await page.locator("text=Fel").all()
        for btn in fel_buttons:
            try:
                if await btn.is_visible():
                    await btn.click()
                    print("Clicked 'Fel' button")
                    break
            except:
                pass
                
        await page.wait_for_timeout(5000)
        
        incident_regions = {}
        
        # Look for the links that say "Visa område"
        links = await page.locator("text=Visa område").all()
        print(f"Found {len(links)} 'Visa område' links")
        
        for i in range(len(links)):
            try:
                # Re-locate to avoid stale element
                current_links = await page.locator("text=Visa område").all()
                if i >= len(current_links): break
                
                link = current_links[i]
                
                # The text is likely in the same row
                row = await link.evaluate_handle("el => el.closest('tr')")
                row_text = await row.evaluate("el => el.innerText")
                
                # Clean up the region name
                # "Stockholms län\tVisa område >" -> "Stockholms län"
                region_name = row_text.split('\n')[0].split('\t')[0].strip()
                print(f"[{i+1}/{len(links)}] Expanding: {region_name}")
                
                # Check if it has 'län' to confirm it's a valid region
                if 'län' not in region_name:
                    continue
                
                # Scroll to it and click
                await link.scroll_into_view_if_needed()
                await link.click()
                await page.wait_for_timeout(3000) # Wait for expansion
                
                # Now the expanded area will contain another table with INCSE IDs
                # We can just get the HTML of the row's immediate sibling or inner accordion
                # Actually, when you click "Visa område", it probably expands a row below it.
                # Let's just find the very next `tr` and get its HTML, or get the whole page HTML again and look for changes.
                
                # Much easier: Just find all visible text or INCSE on the page, 
                # keep track of what we've already seen, and assign the new ones to this region
                current_html = await page.content()
                inc_matches = re.findall(r'INCSE\d+', current_html)
                
                new_count = 0
                for inc_id in set(inc_matches):
                    if inc_id not in incident_regions:
                        incident_regions[inc_id] = region_name
                        new_count += 1
                        
                print(f"  Found {new_count} new incidents for {region_name}")
                
                # We don't necessarily have to close it, just move to the next
                
            except Exception as e:
                print(f"Error on link {i}: {e}")
                
        
        await browser.close()
        
        if not incident_regions:
            print("No incidents mapped!")
            return
            
        print(f"\nTotal unique incidents mapped: {len(incident_regions)}")
        
        # Let's preview specifically Örebro
        orebro_incs = [i for i, reg in incident_regions.items() if 'Örebro' in reg]
        print(f"Örebro Incidents found: {orebro_incs}")
        
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
