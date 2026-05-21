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

from scrapers.telia.fetch_enhanced import scrape_telia_outages
from scrapers.telia.parser_enhanced import parse_telia_outages
from scrapers.telia.mapper_enhanced import map_telia_outages

from scrapers.telenor.fetch import scrape_telenor_outages
from scrapers.telenor.parser import parse_telenor_outage
from scrapers.telenor.mapper import map_to_normalized as map_telenor_outage

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import (
    save_outage, auto_resolve_expired_outages, resolve_missing_outages,
    enrich_missing_geodata, enrich_region_ids, enrich_place_codes, log_scraper_run,
)
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel, ServiceType
from scrapers.common.notify import notify_scraper_failure

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
    """Telia scraper using HTTP (no browser required)."""
    started = datetime.now(timezone.utc)

    def _fetch_and_map():
        raw = scrape_telia_outages()
        parsed = parse_telia_outages(raw)
        return map_telia_outages(parsed)

    result, retries, err = _with_retry(_fetch_and_map)

    if err:
        logger.exception("Telia scraper failed after %d retries", MAX_RETRIES)
        notify_scraper_failure("telia", str(err), started_at=started,
                               finished_at=datetime.now(timezone.utc), retry_count=retries)
        log_scraper_run(db, "telia", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    seen_ids = []
    for item in (result or []):
        try:
            save_outage(db, item, {"source": "telia_http"})
            seen_ids.append(item.incident_id)
        except Exception:
            logger.exception("Failed to save Telia outage %s", item.incident_id)

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TELIA, seen_ids)
    logger.info("Telia: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "telia", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


def _run_telenor_scraper(db):
    """Telenor scraper using HTTP (no browser required)."""
    from scrapers.telenor.parser import parse_telenor_outages
    from scrapers.telenor.mapper import map_telenor_outages
    started = datetime.now(timezone.utc)

    def _fetch_and_map():
        raw = scrape_telenor_outages()
        parsed = parse_telenor_outages(raw)
        return map_telenor_outages(parsed)

    result, retries, err = _with_retry(_fetch_and_map)

    if err:
        logger.exception("Telenor scraper failed after %d retries", MAX_RETRIES)
        notify_scraper_failure("telenor", str(err), started_at=started,
                               finished_at=datetime.now(timezone.utc), retry_count=retries)
        log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    seen_ids = []
    for item in (result or []):
        try:
            save_outage(db, item, {"source": "telenor_http"})
            seen_ids.append(item.incident_id)
        except Exception:
            logger.exception("Failed to save Telenor outage %s", item.incident_id)

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
        notify_scraper_failure(
            "tre",
            str(err),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            retry_count=retries,
        )
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
        # auto_resolve_expired_outages() intentionally removed —
        # delta-based resolution is handled by resolve_missing_outages() per operator.
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
