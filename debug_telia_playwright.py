import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    print("Starting Playwright for visual debugging...")
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
                
        await page.wait_for_timeout(5000) # Wait for accordion to load
        
        # Take a screenshot to see what we are dealing with
        screenshot_path = os.path.join(os.getcwd(), 'telia_debug.png')
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Try to find anything with Visa område or regions
        html = await page.content()
        import re
        reg_matches = re.findall(r'Visa område', html)
        print(f"Found 'Visa område' in HTML {len(reg_matches)} times")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
