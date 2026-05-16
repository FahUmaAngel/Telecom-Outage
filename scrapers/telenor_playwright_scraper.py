"""
Telenor Playwright Scraper
Replaces the Selenium version — handles dynamic content via county expansion.
"""
import logging
import re
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

TELENOR_URL = "https://mboss.telenor.se/coverageportal?appmode=outage"


def _expand_accordion(page) -> bool:
    """Click the 'I följande län' accordion button if collapsed."""
    try:
        btn = page.locator("button:has-text('I följande län'), button#headingOne")
        btn.wait_for(timeout=15000)
        expanded = btn.get_attribute("aria-expanded")
        if expanded != "true":
            logger.info("Clicking to expand accordion...")
            btn.click()
            page.wait_for_timeout(2000)
        return True
    except Exception as e:
        logger.warning(f"Accordion not found: {e}")
        return False


def _get_county_names(page) -> List[str]:
    """Extract county names from the table rows."""
    names = []
    try:
        rows = page.locator("tr:has-text('län')").all()
        for row in rows:
            text = row.inner_text().strip().split("\n")[0]
            text = re.sub(r"Visa.*", "", text).split("(")[0].strip()
            if text:
                names.append(text)
    except Exception as e:
        logger.warning(f"Error reading county rows: {e}")
    return names


def _parse_incident_rows(page, county: str, seen: set) -> List[Dict]:
    """Parse incident rows from the table currently shown."""
    outages = []
    try:
        rows = page.locator("table tbody tr").all()
        for row in rows:
            cells = row.locator("td").all()
            texts = [c.inner_text().strip() for c in cells]
            if len(texts) < 4:
                continue

            incident_id = None
            if re.match(r"^\d{8}$", texts[0]):
                incident_id, desc, start, end = texts[0], texts[1], texts[2], texts[3]
            elif len(texts) >= 5 and re.match(r"^\d{8}$", texts[1]):
                incident_id, desc, start, end = texts[1], texts[2], texts[3], texts[4]

            if incident_id and incident_id not in seen:
                seen.add(incident_id)
                outages.append({
                    "incident_id": incident_id,
                    "operator": "Telenor",
                    "location": county,
                    "description": desc,
                    "start_time": start,
                    "estimated_end": end,
                    "status": "active",
                    "title": incident_id,
                })
                logger.info(f"  + Added incident {incident_id} in {county}")
    except Exception as e:
        logger.warning(f"Error parsing rows for {county}: {e}")
    return outages


def _process_county(page, county: str, seen: set) -> List[Dict]:
    """Reload page, expand accordion, click county zoom icon, parse incidents."""
    try:
        page.goto(TELENOR_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        if not _expand_accordion(page):
            return []

        row = page.locator(f"tr:has-text('{county}')").first
        row.wait_for(timeout=10000)

        zoom = row.locator("i.fa-search, .fa-search").first
        zoom.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        zoom.click()

        logger.info(f"  Waiting for incidents to load for {county}...")
        page.wait_for_timeout(6000)

        found = _parse_incident_rows(page, county, seen)
        if not found:
            logger.info(f"  No new incidents found for {county}")
        return found
    except Exception as e:
        logger.warning(f"  Error processing county {county}: {e}")
        return []


def scrape_telenor_with_playwright() -> Dict:
    """Scrape Telenor outages using Playwright. Same return shape as Selenium version."""
    from playwright.sync_api import sync_playwright

    logger.info("=" * 60)
    logger.info("Telenor Playwright Scraper")
    logger.info("=" * 60)

    results = {
        "outages": [],
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "method": "playwright_telenor",
    }
    seen: set = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()

        try:
            logger.info(f"Loading: {TELENOR_URL}")
            page.goto(TELENOR_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(5000)

            _expand_accordion(page)
            counties = _get_county_names(page)

            if not counties:
                logger.warning("No counties found — falling back to regex on page source")
                ids = set(re.findall(r"\b\d{8}\b", page.content()))
                for i in ids:
                    results["outages"].append({"incident_id": i, "operator": "Telenor",
                                               "location": "Sverige", "status": "active"})
            else:
                logger.info(f"Found {len(counties)} counties")
                for idx, county in enumerate(counties):
                    logger.info(f"Processing county {idx + 1}/{len(counties)}: {county}")
                    results["outages"].extend(_process_county(page, county, seen))

            results["success"] = len(results["outages"]) > 0

        except Exception as e:
            logger.exception(f"Critical error: {e}", exc_info=True)
            results["error"] = str(e)
        finally:
            browser.close()

    logger.info("=" * 60)
    logger.info(f"Result: {'SUCCESS' if results['success'] else 'FAILED'}")
    logger.info(f"Total outages: {len(results['outages'])}")
    logger.info("=" * 60)
    return results


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, encoding='utf-8')
    res = scrape_telenor_with_playwright()
    with open("telenor_playwright_results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print("Saved to telenor_playwright_results.json")
