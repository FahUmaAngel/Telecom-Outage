import asyncio
from playwright.async_api import async_playwright
import sqlite3
import re
import sys
import os

sys.path.append(os.getcwd())
try:
    from scrapers.common.geocoding import get_county_coordinates
except:
    def get_county_coordinates(county_name, jitter=False):
        return (58.0, 14.0)

async def run():
    print("Starting fast Playwright extraction to completely fix Telia DB...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        await page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
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
                
        await page.wait_for_timeout(4000)
        
        incident_regions = {}
        
        # Get all region links
        links = await page.locator("a:has-text('Visa område')").all()
        if not links:
            links = await page.locator("button:has-text('Visa område')").all()
            if not links:
                links = await page.locator("text=Visa område").all()
                
        print(f"Found {len(links)} regional links")
        
        # We process one by one
        for i in range(len(links)):
            try:
                current_links = await page.locator("text=Visa område").all()
                if i >= len(current_links): break
                link = current_links[i]
                
                # Extract Region Name
                row = await link.evaluate_handle("el => el.closest('tr')")
                text = await row.evaluate("el => el.innerText")
                reg_name = text.split('\\n')[0].split('\\t')[0].split('Visa område')[0].strip()
                
                if 'län' not in reg_name:
                    continue
                    
                print(f"[{i+1}/{len(links)}] Scraping {reg_name}...")
                
                # Scroll to it
                await link.scroll_into_view_if_needed()
                await link.click()
                await page.wait_for_timeout(2000) # Let it expand
                
                # Extract incidents under this region
                # When expanded, the next sibling row contains the incident table
                html = await page.evaluate(
                    "(el) => { const next = el.nextElementSibling; return next ? next.innerHTML : ''; }", 
                    row
                )
                
                if html:
                    ids = re.findall(r'INCSE\d+', html)
                    for inc in set(ids):
                        if inc not in incident_regions:
                            incident_regions[inc] = reg_name
                            
            except Exception as e:
                print(f"Error on {i}: {e}")
                
        await browser.close()
        
        print(f"Total mapped incidents: {len(incident_regions)}")
        orebro = [k for k, v in incident_regions.items() if 'Örebro' in v]
        print(f"Örebro Incidents: {orebro}")
        
        if not incident_regions: return
        
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
        print(f"Done. Fixed {updated} DB records.")

if __name__ == "__main__":
    asyncio.run(run())
