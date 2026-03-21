import asyncio
from playwright.async_api import async_playwright

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

async def scrape_dom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="sv-SE"
        )
        page = await context.new_page()

        print("Navigating...")
        await page.goto(TELE2_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        print("Accepting cookies...")
        for sel in ["button:has-text('Acceptera alla')", "button:has-text('Acceptera')"]:
            kw = page.locator(sel)
            if await kw.count() > 0 and await kw.first.is_visible():
                await kw.first.click()
                await page.wait_for_timeout(2000)
                break

        print("Finding disturbance list toggle...")
        toggles = [
            "button:has-text('Pågående störningar')",
            "button:has-text('störning')",
            "[aria-label*='störning']"
        ]
        
        clicked = False
        for sel in toggles:
            loc = page.locator(sel)
            if await loc.count() > 0 and await loc.first.is_visible():
                await loc.first.click()
                print(f"Clicked: {sel}")
                clicked = True
                await page.wait_for_timeout(4000)
                break

        if not clicked:
            print("WARNING: Could not find or click the disturbance list button. Trying to extract any tables found...")
            
        print("Extracting tabular data...")
        # Since it's a React/Astro list, it might be a <table> or <ul>
        # Let's extract all text content from the disturbance panel
        try:
            # We look for containers that might hold the tickets
            html = await page.content()
            if "Störningsnr" in html or "Beräknad sluttid" in html:
                print("FOUND TICKET HEADERS IN HTML!")
                
                # Let's grab the specific nodes
                # Translation said: ticketNumber: "Störningsnr", location: "Plats"
                elements = await page.evaluate('''() => {
                    const results = [];
                    // Find rows or cards containing 'Störningsnr'
                    const items = Array.from(document.querySelectorAll('div, tr, li')).filter(el => el.innerText.includes('Störningsnr') && el.innerText.includes('Plats'));
                    for (const item of items) {
                        results.push(item.innerText);
                    }
                    return results;
                }''')
                
                print(f"Found {len(elements)} raw tickets/containers.")
                for idx, text in enumerate(elements):
                    print(f"\n--- Item {idx} ---")
                    print(text)
            else:
                print("No ticket headers found in HTML.")
                
        except Exception as e:
            print("Extraction error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dom())
