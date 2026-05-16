import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.db.connection import SessionLocal
from scrapers.telia_playwright_recovery import (
    COVERAGE_PORTAL_URL,
    handle_recovery_response,
    process_incidents,
    setup_context,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("TeliaPlaywrightBackfill")


def trigger_date_navigation(page, target_date_str: str) -> bool:
    try:
        page.wait_for_selector(".timeline-radio-btn-historical", timeout=10000)
        page.locator(".timeline-radio-btn-historical").first.click(timeout=5000)
        page.wait_for_timeout(2000)

        date_input = page.locator(".focus-date-selector input, .input-group.date input").first
        date_input.click(timeout=5000)
        date_input.fill(target_date_str)
        page.evaluate(
            """([selector, dateStr]) => {
                const el = document.querySelector(selector);
                if (!el) return false;
                el.removeAttribute('disabled');
                el.value = dateStr;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                if (window.jQuery) {
                    window.jQuery(el).trigger('change');
                }
                return true;
            }""",
            [".focus-date-selector input, .input-group.date input", target_date_str],
        )
        date_input.press("Enter")
        page.wait_for_timeout(5000)
        return True
    except Exception as error:
        logger.warning("Nav fail for %s: %s", target_date_str, error)
        return False


def run_backfill(start_date: datetime, end_date: datetime) -> None:
    db = SessionLocal()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = setup_context(browser)
            page = context.new_page()
            captured = []
            page.on("response", lambda response: handle_recovery_response(response, captured))

            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                logger.info("Recovering %s...", date_str)
                page.goto(COVERAGE_PORTAL_URL, wait_until="networkidle")

                if trigger_date_navigation(page, date_str):
                    process_incidents(db, captured, date_str)
                    captured.clear()

                current += timedelta(days=1)

            browser.close()
    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill Telia historical data for a date range.")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_backfill(
        start_date=datetime.strptime(arguments.start_date, "%Y-%m-%d"),
        end_date=datetime.strptime(arguments.end_date, "%Y-%m-%d"),
    )
