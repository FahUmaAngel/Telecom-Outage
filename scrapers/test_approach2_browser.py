"""
Approach 2: Browser Automation with Playwright
Use browser to interact with page and capture dynamic content
"""
import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_with_playwright():
    """
    Use Playwright to load page and extract outage data.
    """
    results = {
        'success': False,
        'outages': [],
        'error': None
    }
    
    try:
        async with async_playwright() as p:
            logger.info("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to page
            url = "https://www.telia.se/foretag/support/driftinformation?category=mobila-natet"
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle")
            
            # Wait for content to load
            logger.info("Waiting for content to load...")
            await asyncio.sleep(3)
            
            # Try to find outage elements
            logger.info("Searching for outage elements...")
            
            # Look for common selectors
            selectors_to_try = [
                '[data-testid*="outage"]',
                '[class*="outage"]',
                '[class*="incident"]',
                '[class*="drift"]',
                'article',
                '[role="article"]',
            ]
            
            for selector in selectors_to_try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for i, elem in enumerate(elements[:5]):  # First 5
                        text = await elem.inner_text()
                        if text and len(text) > 20:
                            results['outages'].append({
                                'selector': selector,
                                'text': text[:200]
                            })
            
            # Capture screenshot
            logger.info("Capturing screenshot...")
            await page.screenshot(path='telia_playwright_screenshot.png')
            
            # Get page content
            content = await page.content()
            with open('telia_playwright_html.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            await browser.close()
            
            results['success'] = True
            logger.info(f"✓ Browser automation completed. Found {len(results['outages'])} potential outages")
            
    except Exception as e:
        results['error'] = str(e)
        logger.error(f"✗ Browser automation failed: {e}")
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("APPROACH 2: Browser Automation (Playwright)")
    print("=" * 60)
    
    print("\nLaunching browser automation...")
    results = asyncio.run(scrape_with_playwright())
    
    if results['success']:
        print(f"\n✓ SUCCESS: Browser automation completed")
        print(f"  Found {len(results['outages'])} potential outage elements")
        
        if results['outages']:
            print("\nSample outages:")
            for i, outage in enumerate(results['outages'][:3], 1):
                print(f"\n  {i}. Selector: {outage['selector']}")
                print(f"     Text: {outage['text'][:100]}...")
        
        print("\n✓ Saved screenshot to: telia_playwright_screenshot.png")
        print("✓ Saved HTML to: telia_playwright_html.html")
    else:
        print(f"\n✗ FAILED: {results['error']}")
    
    # Save results
    with open('approach2_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("RESULT: Approach 2 - " + ("SUCCESS" if results['success'] else "FAILED"))
    print("=" * 60)
