import asyncio
from playwright.async_api import async_playwright
import sqlite3
import sys
import os

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

async def run():
    print("Starting Playwright JS extraction...")
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
                
        await page.wait_for_timeout(5000)
        
        # We inject JS to find all accordion wrappers or table containers
        # From screenshot we know:
        # <tr>
        #   <td>Stockholms län</td>
        #   <td><a>Visa område</a></td>
        # </tr>
        # The incidents are likely in a sibling row or inside an accordion.
        
        mapping_result = await page.evaluate("""
            () => {
                const results = {};
                // Find all 'Visa område' links
                const links = Array.from(document.querySelectorAll('a, button')).filter(el => el.innerText && el.innerText.includes('Visa område'));
                
                links.forEach(link => {
                    const row = link.closest('tr');
                    if (!row) return;
                    
                    const regionName = row.innerText.split('\\n')[0].split('\\t')[0].trim();
                    if (!regionName || !regionName.includes('län')) return;
                    
                    // The incidents table is usually the immediate next row (a collapsible detail row)
                    const nextRow = row.nextElementSibling;
                    if (nextRow) {
                        // Look for all INCSE inside this next row
                        const html = nextRow.innerHTML;
                        const ids = [...html.matchAll(/INCSE\\d+/g)].map(m => m[0]);
                        if (ids.length > 0) {
                            results[regionName] = [...new Set(ids)];
                        }
                    }
                });
                return results;
            }
        """)
        
        await browser.close()
        
        incident_regions = {}
        for region, ids in mapping_result.items():
            for inc in ids:
                incident_regions[inc] = region
                
        if not incident_regions:
            print("No incidents mapped! The DOM structure might differ.")
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
