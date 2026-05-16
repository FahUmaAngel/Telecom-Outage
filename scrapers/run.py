"""
Main scraper runner.
Executes all scrapers and saves to DB.
"""
import logging
import time
from datetime import datetime, timezone

from scrapers.tre.fetch import scrape_tre_outages
from scrapers.tre.parser import parse_tre_outages
from scrapers.tre.mapper import map_tre_outages

from scrapers.telia import scrape_portal_granular

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import (
    save_outage, auto_resolve_expired_outages, resolve_missing_outages,
    enrich_missing_geodata, enrich_region_ids, enrich_place_codes, log_scraper_run,
)
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES, create_bilingual_text
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status, parse_swedish_date

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
)
logger = logging.getLogger("ScraperRunner")

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds, doubles each attempt


def _with_retry(fn, *args, **kwargs):
    """Run fn with exponential-backoff retry. Returns (result, retry_count, error)."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs), attempt, None
        except Exception as exc:
            last_err = exc
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning("%s attempt %d/%d failed: %s. Retrying in %ds...",
                               fn.__name__, attempt + 1, MAX_RETRIES, exc, wait)
                time.sleep(wait)
    return None, MAX_RETRIES - 1, last_err


def _run_telia_scraper(db):
    """Telia scraper with retry and health logging."""
    started = datetime.now(timezone.utc)
    result, retries, err = _with_retry(scrape_portal_granular)

    if err:
        logger.exception("Telia scraper failed after %d retries", MAX_RETRIES)
        log_scraper_run(db, "telia", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    seen_ids = result or []
    resolved = resolve_missing_outages(db, OperatorEnum.TELIA, seen_ids)
    logger.info("Telia: delta-resolved %d vanished incidents", resolved)
    log_scraper_run(db, "telia", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


def _process_telenor_outage(db, outage):
    """Process and save a single Telenor outage."""
    location_text = outage.get('location', '')
    desc_text = outage.get('description', '')
    title_text = outage.get('title', f"Incident {outage['incident_id']}")
    context_text = f"{location_text} {desc_text} {title_text}"

    normalized = NormalizedOutage(
        operator=OperatorEnum.TELENOR,
        incident_id=outage['incident_id'],
        title={"sv": outage['incident_id'], "en": outage['incident_id']},
        description=create_bilingual_text(desc_text or f"Incident ID: {outage['incident_id']}"),
        location=location_text or 'Unknown',
        status=classify_status(context_text, OutageStatus.ACTIVE),
        severity=SeverityLevel.MEDIUM,
        affected_services=[s for s in classify_services(context_text) if s.value not in ['voice', 'data']],
        source_url="https://mboss.telenor.se/coverageportal?appmode=outage",
        started_at=parse_swedish_date(outage.get('start_time')),
        estimated_fix_time=parse_swedish_date(outage.get('estimated_end'))
    )

    search_text = location_text if location_text else context_text
    county_name = extract_region_from_text(search_text, SWEDISH_COUNTIES)
    if county_name:
        normalized.location = county_name
        coords = get_county_coordinates(county_name, jitter=True)
        if coords:
            normalized.latitude, normalized.longitude = coords

    save_outage(db, normalized, {"source": "telenor_selenium", "raw": outage})


def _run_telenor_scraper(db):
    """Telenor scraper with retry and health logging."""
    from scrapers.telenor_playwright_scraper import scrape_telenor_with_playwright
    started = datetime.now(timezone.utc)
    result, retries, err = _with_retry(scrape_telenor_with_playwright)

    if err:
        logger.exception("Telenor scraper failed after %d retries", MAX_RETRIES)
        log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    if not result.get('success'):
        logger.error("Telenor scraper returned failure response")
        log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message="success=False")
        return

    seen_ids = []
    for outage in result['outages']:
        try:
            _process_telenor_outage(db, outage)
            seen_ids.append(str(outage['incident_id']))
        except Exception:
            logger.exception("Failed to process Telenor outage %s", outage.get('incident_id'))

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TELENOR, seen_ids)
    logger.info("Telenor: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


def _run_tre_scraper(db):
    """Tre scraper with retry and health logging."""
    started = datetime.now(timezone.utc)

    def _fetch_and_map():
        raw = scrape_tre_outages()
        parsed = parse_tre_outages(raw)
        return map_tre_outages(parsed)

    result, retries, err = _with_retry(_fetch_and_map)

    if err:
        logger.exception("Tre scraper failed after %d retries", MAX_RETRIES)
        db.rollback()
        log_scraper_run(db, "tre", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    seen_ids = []
    for item in result:
        save_outage(db, item, {"source": "tre_scraper"})
        seen_ids.append(item.incident_id)

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TRE, seen_ids)
    logger.info("Tre: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "tre", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


def run_scrapers():
    """Main entry point — runs all scrapers then enrichment passes."""
    logger.info("Starting scraper run...")
    db = SessionLocal()
    try:
        _run_telia_scraper(db)
        _run_telenor_scraper(db)
        _run_tre_scraper(db)
        resolved = auto_resolve_expired_outages(db)
        if resolved:
            logger.info("Auto-resolved %d expired outages", resolved)
        enriched = enrich_missing_geodata(db)
        if enriched:
            logger.info("Enriched geodata for %d records", enriched)
        region_filled = enrich_region_ids(db)
        if region_filled:
            logger.info("Filled region_id for %d records", region_filled)
        place_filled = enrich_place_codes(db)
        if place_filled:
            logger.info("Filled place code for %d records", place_filled)
    finally:
        db.close()
    logger.info("Scraper run completed.")


if __name__ == "__main__":
    run_scrapers()
