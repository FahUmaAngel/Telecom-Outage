"""
Playwright-based Telia Scraper
Modern alternative to Selenium with better performance and reliability.
"""
import json
import logging
import re
from typing import List, Dict
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COVERAGE_PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"


def extract_incidents_from_content(content: str) -> List[Dict]:
    """Extract incident information from page content."""
    incidents = []
    
    incident_ids = re.findall(r'INCSE\d+', content)
    incident_ids = list(set(incident_ids))
    
    for inc_id in incident_ids:
        incident = {
            'incident_id': inc_id,
            'operator': 'Telia',
            'source': 'coverage_portal',
            'status': 'active'
        }
        
        # Extract context
        pattern = rf'{inc_id}[^<]*(?:<[^>]+>[^<]*)*?(?:(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)[^<]*\d{{2}}:\d{{2}})'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            context = matches[0][:300]
            date_pattern = r'((?:Sat|Sun|Mon|Tue|Wed|Thu|Fri),?\s+\w+\s+\d+,?\s+\d{2}:\d{2})'
            dates = re.findall(date_pattern, context)
            if dates:
                incident['start_time'] = dates[0]
                if len(dates) > 1:
                    incident['estimated_end'] = dates[1]
        
        incidents.append(incident)
    
    return incidents


def scrape_with_playwright() -> Dict:
    """Scrape using Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'outages': [],
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium',
            'success': False
        }
    
    logger.info("="*60)
    logger.info("Telia Playwright Scraper")
    logger.info("="*60)
    
    results = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': 'playwright'
    }
    
    try:
        with sync_playwright() as p:
            logger.info("Launching browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            logger.info(f"Loading: {COVERAGE_PORTAL_URL}")
            page.goto(COVERAGE_PORTAL_URL, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(5000)  # Extra wait for JS
            
            # Click "Fel" button
            try:
                fel_button = page.locator("text=Fel").first
                if fel_button.is_visible():
                    fel_button.click()
                    logger.info("✓ Clicked 'Fel' button")
                    page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"Could not click 'Fel': {e}")
            
            # Extract initial incidents
            content = page.content()
            initial_incidents = extract_incidents_from_content(content)
            logger.info(f"Found {len(initial_incidents)} incidents initially")
            results['outages'].extend(initial_incidents)
            
            # Expand regions
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                page.wait_for_timeout(1000)
                
                # Get all "Visa område" buttons
                buttons = page.locator("text=Visa område").all()
                logger.info(f"Found {len(buttons)} region buttons")
                
                max_clicks = min(5, len(buttons))
                for i in range(max_clicks):
                    try:
                        logger.info(f"Clicking region {i+1}/{max_clicks}...")
                        
                        # Re-locate button to avoid stale references
                        button = page.locator("text=Visa område").nth(i)
                        button.scroll_into_view_if_needed()
                        button.click()
                        page.wait_for_timeout(3000)
                        
                        # Extract new incidents
                        new_content = page.content()
                        new_incidents = extract_incidents_from_content(new_content)
                        
                        # Add unique incidents
                        existing_ids = {o['incident_id'] for o in results['outages']}
                        for inc in new_incidents:
                            if inc['incident_id'] not in existing_ids:
                                results['outages'].append(inc)
                                existing_ids.add(inc['incident_id'])
                        
                        logger.info(f"  Total unique: {len(results['outages'])}")
                        
                    except Exception as e:
                        logger.warning(f"  Error at region {i+1}: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error expanding regions: {e}")
            
            # Save artifacts
            page.screenshot(path='telia_playwright_screenshot.png')
            with open('telia_playwright_final.html', 'w', encoding='utf-8') as f:
                f.write(page.content())
            logger.info("✓ Saved screenshot and HTML")
            
            browser.close()
        
        results['success'] = len(results['outages']) > 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        results['error'] = str(e)
    
    logger.info("\n" + "="*60)
    logger.info(f"Result: {'SUCCESS' if results['success'] else 'FAILED'}")
    logger.info(f"Total outages: {len(results['outages'])}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    results = scrape_with_playwright()
    
    output_file = "telia_playwright_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Saved to: {output_file}")
    
    if results['outages']:
        logger.info(f"\n📊 Found {len(results['outages'])} outages:")
        for i, outage in enumerate(results['outages'][:5], 1):
            logger.info(f"\n  {i}. {outage['incident_id']}")
            if 'start_time' in outage:
                logger.info(f"     Start: {outage.get('start_time', 'N/A')}")
            if 'estimated_end' in outage:
                logger.info(f"     End: {outage.get('estimated_end', 'N/A')}")
        
        if len(results['outages']) > 5:
            logger.info(f"\n  ... and {len(results['outages']) - 5} more")
