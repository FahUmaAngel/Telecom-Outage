import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    print("Starting Playwright to dump DOM...")
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
        
        # Expand ALL links so the entire DOM is hydrated
        links = await page.locator("text=Visa område").all()
        print(f"Expanding {len(links)} links...")
        for link in links:
            try:
                await link.scroll_into_view_if_needed()
                await link.click()
                await page.wait_for_timeout(1000)
            except:
                pass
                
        # Wait a bit more for tables to render
        await page.wait_for_timeout(3000)
        
        # Dump HTML
        html = await page.content()
        with open('telia_full_dom.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("DOM dumped to telia_full_dom.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
