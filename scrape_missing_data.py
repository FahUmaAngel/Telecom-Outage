"""
Scrape missing data for Telia, Telenor, Tre from 2026-04-30 to present.

Strategy
--------
1. Run live scrapers for Telia, Telenor, Tre to capture currently-visible
   outages (incidents started before now and still active/recent).
2. Run Telia 'Nätverkshistorik' historical scraper to recover resolved
   incidents in the gap window.
3. Persist everything via the existing CRUD layer (save_outage), which
   handles deduplication.

NOTE: Telenor and Tre do not expose a historical archive on their public
sites. We can only capture what their portals currently display, so any
short-lived incident that was already cleared before today is NOT
recoverable through scraping. Tre incidents that started before 2026-04-30
and are still open WILL be picked up. Same for Telenor.
"""
from __future__ import annotations

import logging
from datetime import datetime

from scrapers.db.connection import SessionLocal
from scrapers.run import _run_telia_scraper, _run_telenor_scraper, _run_tre_scraper
from scrapers.historical_scraper import scrape_telia_history
from scrapers.db.crud import save_outage
from scrapers.common.models import (
    NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
)
from scrapers.common.translation import SWEDISH_COUNTIES, create_bilingual_text
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.engine import (
    extract_region_from_text, classify_services, classify_status, parse_swedish_date
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ScrapeMissing")

GAP_START = datetime(2026, 4, 30)
GAP_END = datetime.now()

TELIA_HISTORY_URL = (
    "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
)


def _save_telia_history_outage(db, item: dict) -> bool:
    """Persist a single Telia historical incident via save_outage."""
    inc_id = item.get("incident_id")
    if not inc_id:
        return False

    desc_text = item.get("description") or f"Historical incident {inc_id}"
    location_text = item.get("location") or "Sverige"
    context_text = f"{inc_id} {location_text} {desc_text}"

    normalized = NormalizedOutage(
        operator=OperatorEnum.TELIA,
        incident_id=inc_id,
        title={"sv": inc_id, "en": inc_id},
        description=create_bilingual_text(desc_text),
        location=location_text,
        status=classify_status(context_text, OutageStatus.RESOLVED),
        severity=SeverityLevel.MEDIUM,
        affected_services=classify_services(context_text),
        source_url=TELIA_HISTORY_URL,
        started_at=parse_swedish_date(item.get("start_time")),
        estimated_fix_time=parse_swedish_date(item.get("estimated_end")),
    )

    county_name = extract_region_from_text(
        f"{location_text} {desc_text}", SWEDISH_COUNTIES
    )
    if county_name:
        normalized.location = county_name
        coords = get_county_coordinates(county_name, jitter=True)
        if coords:
            normalized.latitude, normalized.longitude = coords

    save_outage(
        db,
        normalized,
        {"source": "telia_history", "raw": item, "backfill": True},
    )
    return True


def run_live_snapshot():
    """Run live scrapers for Telia, Telenor, Tre (captures current state)."""
    logger.info("=" * 70)
    logger.info("PHASE 1: Live snapshot scrape (Telia, Telenor, Tre)")
    logger.info("=" * 70)

    db = SessionLocal()
    try:
        logger.info("--- Telia (live) ---")
        _run_telia_scraper(db)

        logger.info("--- Telenor (live) ---")
        _run_telenor_scraper(db)

        logger.info("--- Tre (live) ---")
        _run_tre_scraper(db)
    finally:
        db.close()


def run_telia_backfill():
    """Backfill Telia using Nätverkshistorik between GAP_START and GAP_END."""
    logger.info("=" * 70)
    logger.info(
        "PHASE 2: Telia historical backfill %s -> %s",
        GAP_START.date(), GAP_END.date(),
    )
    logger.info("=" * 70)

    result = scrape_telia_history(GAP_START, GAP_END)
    outages = result.get("outages", [])
    logger.info("Telia history scraper returned %d incidents", len(outages))

    if not outages:
        logger.warning("No historical incidents returned from Telia portal")
        return

    db = SessionLocal()
    saved = 0
    try:
        for item in outages:
            try:
                if _save_telia_history_outage(db, item):
                    saved += 1
            except Exception as exc:
                logger.warning(
                    "Failed to save Telia historical incident %s: %s",
                    item.get("incident_id"), exc,
                )
        db.commit()
        logger.info("Telia backfill: persisted %d incidents", saved)
    except Exception as exc:
        logger.error("Telia backfill commit failed: %s", exc, exc_info=True)
        db.rollback()
    finally:
        db.close()


def main():
    logger.info("Target gap window: %s -> %s",
                GAP_START.isoformat(), GAP_END.isoformat())

    run_live_snapshot()
    run_telia_backfill()

    logger.info("=" * 70)
    logger.info("DONE. Verify with: python scratch/check_db.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()