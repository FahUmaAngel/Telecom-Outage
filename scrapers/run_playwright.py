"""
Playwright-based scraper runner — designed for GitHub Actions.
Uses real browser for Telia and Telenor (required for JS-rendered portals),
HTTP for Tre.
"""
import logging
import time
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import (
    save_outage, resolve_missing_outages, auto_resolve_expired_outages,
    enrich_missing_geodata, enrich_region_ids, enrich_place_codes, log_scraper_run,
)
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel, ServiceType
from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.translation import SWEDISH_COUNTIES, create_bilingual_text
from scrapers.common.engine import extract_region_from_text, classify_services, classify_status, parse_swedish_date
from scrapers.common.notify import notify_scraper_failure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("PlaywrightScraper")

MAX_RETRIES = 3
RETRY_DELAY = 2


def _with_retry(fn, *args, **kwargs):
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


# ---------------------------------------------------------------------------
# Telia
# ---------------------------------------------------------------------------

def _map_telia_incident(item: dict) -> NormalizedOutage:
    """Map raw Telia AreaTicketList dict → NormalizedOutage."""
    import re, json as _json
    from datetime import datetime as _dt

    inc_id = str(item.get("ExternalId", ""))
    county_name = item.get("CountyName") or ""
    if county_name.lower() == "unknown":
        county_name = ""

    # Coordinates from BBox
    bbox = item.get("BBox", {})
    ll = bbox.get("LL", {})
    lat = ll.get("Northing") or item.get("Northing")
    lon = ll.get("Easting") or item.get("Easting")
    if not lat or not lon:
        county_geo = f"{county_name} län" if county_name and "län" not in county_name.lower() else county_name
        coords = get_county_coordinates(county_geo, jitter=True)
        lat, lon = coords if coords else (58.0, 14.0)

    # Location
    area_name = item.get("AreaName") or ""
    raw_location = ", ".join(p for p in [area_name, county_name] if p)
    location = extract_region_from_text(raw_location, SWEDISH_COUNTIES) or county_name or area_name or "Unknown"

    # Dates
    def _clean_date(val):
        if not val:
            return None
        if isinstance(val, str) and "/Date(" in val:
            m = re.search(r"\d+", val)
            if m:
                return _dt.fromtimestamp(int(m.group()) / 1000).isoformat() + "+01:00"
        return parse_swedish_date(val) if isinstance(val, str) and len(val) > 5 else None

    started_at = _clean_date(item.get("StartTimeStr") or item.get("EventTime"))
    estimated_fix = _clean_date(item.get("EstimatedEndTimeStr") or item.get("EstimatedCloseTime"))

    # Services
    desc_raw = item.get("Description") or item.get("Text") or ""
    services_text = desc_raw + " " + item.get("AffectedServices", "")
    t = services_text.lower()
    service_map = {"5g": ServiceType.MOBILE_5G, "4g": ServiceType.MOBILE_4G, "2g": ServiceType.MOBILE_2G}
    affected = list({service_map[k] for k in service_map if k in t})
    if not affected:
        affected = [ServiceType.MOBILE_4G]

    return NormalizedOutage(
        operator=OperatorEnum.TELIA,
        incident_id=inc_id,
        title={"sv": inc_id, "en": inc_id},
        description={"sv": desc_raw, "en": desc_raw},
        location=location,
        status=OutageStatus.ACTIVE,
        severity=SeverityLevel.MEDIUM,
        affected_services=affected,
        source_url="https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage",
        started_at=started_at,
        estimated_fix_time=estimated_fix,
        latitude=float(lat) if lat else None,
        longitude=float(lon) if lon else None,
    )


def _run_telia(db):
    from scrapers.telia.portal_scraper import scrape_portal_granular
    started = datetime.now(timezone.utc)

    result, retries, err = _with_retry(scrape_portal_granular)

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
            normalized = _map_telia_incident(item)
            save_outage(db, normalized, {"source": "telia_playwright", "raw": item})
            seen_ids.append(normalized.incident_id)
        except Exception:
            logger.exception("Failed to process Telia incident %s", item.get("ExternalId"))

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TELIA, seen_ids)
    logger.info("Telia: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "telia", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


# ---------------------------------------------------------------------------
# Telenor
# ---------------------------------------------------------------------------

def _run_telenor(db):
    from scrapers.telenor_playwright_scraper import scrape_telenor_with_playwright
    started = datetime.now(timezone.utc)

    result, retries, err = _with_retry(scrape_telenor_with_playwright)

    if err or not (result or {}).get("success"):
        msg = str(err) if err else "success=False"
        logger.error("Telenor scraper failed: %s", msg)
        notify_scraper_failure("telenor", msg, started_at=started,
                               finished_at=datetime.now(timezone.utc), retry_count=retries)
        log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=msg)
        return

    seen_ids = []
    for outage in result.get("outages", []):
        try:
            location_text = outage.get("location", "")
            desc_text = outage.get("description", "")
            inc_id = str(outage.get("incident_id", ""))
            context = f"{location_text} {desc_text} {inc_id}"

            normalized = NormalizedOutage(
                operator=OperatorEnum.TELENOR,
                incident_id=inc_id,
                title={"sv": inc_id, "en": inc_id},
                description=create_bilingual_text(desc_text or f"Incident {inc_id}"),
                location=location_text or "Unknown",
                status=classify_status(context, OutageStatus.ACTIVE),
                severity=SeverityLevel.MEDIUM,
                affected_services=classify_services(context),
                source_url="https://mboss.telenor.se/coverageportal?appmode=outage",
                started_at=parse_swedish_date(outage.get("start_time")),
                estimated_fix_time=parse_swedish_date(outage.get("estimated_end")),
            )

            county = extract_region_from_text(location_text or context, SWEDISH_COUNTIES)
            if county:
                normalized.location = county
                coords = get_county_coordinates(county, jitter=True)
                if coords:
                    normalized.latitude, normalized.longitude = coords

            save_outage(db, normalized, {"source": "telenor_playwright", "raw": outage})
            seen_ids.append(inc_id)
        except Exception:
            logger.exception("Failed to process Telenor outage %s", outage.get("incident_id"))

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TELENOR, seen_ids)
    logger.info("Telenor: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "telenor", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


# ---------------------------------------------------------------------------
# Tre (HTTP — same as run.py)
# ---------------------------------------------------------------------------

def _run_tre(db):
    from scrapers.tre.fetch import scrape_tre_outages
    from scrapers.tre.parser import parse_tre_outages
    from scrapers.tre.mapper import map_tre_outages
    started = datetime.now(timezone.utc)

    def _fetch():
        return map_tre_outages(parse_tre_outages(scrape_tre_outages()))

    result, retries, err = _with_retry(_fetch)

    if err:
        logger.exception("Tre scraper failed after %d retries", MAX_RETRIES)
        db.rollback()
        notify_scraper_failure("tre", str(err), started_at=started,
                               finished_at=datetime.now(timezone.utc), retry_count=retries)
        log_scraper_run(db, "tre", started, datetime.now(timezone.utc),
                        "failed", retry_count=retries, error_message=str(err))
        return

    seen_ids = []
    for item in (result or []):
        save_outage(db, item, {"source": "tre_scraper"})
        seen_ids.append(item.incident_id)

    db.commit()
    resolved = resolve_missing_outages(db, OperatorEnum.TRE, seen_ids)
    logger.info("Tre: %d outages, delta-resolved %d", len(seen_ids), resolved)
    log_scraper_run(db, "tre", started, datetime.now(timezone.utc),
                    "success", outages_found=len(seen_ids),
                    outages_resolved=resolved, retry_count=retries)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    logger.info("=== GitHub Actions Scraper Run ===")
    db = SessionLocal()
    try:
        _run_telia(db)
        _run_telenor(db)
        _run_tre(db)
        # Fallback: resolve outages with past ETA (>24h grace) and no end_time
        # that slipped through resolve_missing_outages (e.g. from failed scrape cycles)
        resolved = auto_resolve_expired_outages(db)
        if resolved:
            logger.info("Auto-resolved %d zombie outages (ETA passed >24h, no end_time)", resolved)
        enrich_missing_geodata(db)
        enrich_region_ids(db)
        enrich_place_codes(db)
    finally:
        db.close()
    logger.info("=== Scraper Run Complete ===")


if __name__ == "__main__":
    run()
