"""
Comprehensive Tele2 network interceptor.
Accept cookies, then interact with the page to trigger the ticket list API call.
"""
import asyncio
import json
from playwright.async_api import async_playwright

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

async def capture():
    all_responses = {}
    all_requests = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="sv-SE",
        )
        page = await context.new_page()

        async def on_request(req):
            if "tele2" in req.url or "mim" in req.url.lower():
                all_requests[req.url] = req.headers

        async def on_response(res):
            url = res.url
            ct = res.headers.get("content-type", "")
            if "json" in ct:
                try:
                    data = await res.json()
                    all_responses[url] = data
                    print(f"  JSON: {url[:80]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        print("Loading page...")
        try:
            await page.goto(TELE2_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"goto: {e}")

        await page.wait_for_timeout(3000)

        # Accept cookies
        try:
            for sel in ["button:has-text('Acceptera alla')", "button:has-text('Acceptera')", "#accept-all", ".cookie-accept"]:
                loc = page.locator(sel)
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print(f"Clicked cookie: {sel}")
                    await page.wait_for_timeout(2000)
                    break
        except Exception:
            pass

        # Wait for the map to load and initialize
        await page.wait_for_timeout(6000)

        # Try to click on disturbance list button
        list_selectors = [
            "button:has-text('Pågående störningar')",
            "button:has-text('störning')",
            "[aria-label*='störning']",
            "[data-testid*='disturbance']",
        ]
        for sel in list_selectors:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print(f"Clicked: {sel}")
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        # Wait for any lazy loaded API calls
        await page.wait_for_timeout(5000)

        await browser.close()

    print("\n\n=== ALL CAPTURED RESPONSES ===")
    for url, data in all_responses.items():
        print(f"\n--- {url} ---")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

    print("\n\n=== ALL CAPTURED URLS ===")
    for url in all_responses:
        print(url)

if __name__ == "__main__":
    asyncio.run(capture())
