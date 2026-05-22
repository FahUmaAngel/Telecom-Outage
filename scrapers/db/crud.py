"""
Database CRUD operations.
"""
from sqlalchemy.orm import Session
from typing import Optional
from .models import Outage, RawData, Operator, Region, ScraperRun
from ..common.models import NormalizedOutage, OperatorEnum
from ..common.translation import SWEDISH_COUNTIES
from ..common.engine import extract_region_from_text
from datetime import datetime, timezone, timedelta
import json

from sqlalchemy import func

def get_operator_id(db: Session, operator_name: str) -> Optional[int]:
    op = db.query(Operator).filter(func.lower(Operator.name) == operator_name.lower()).first()
    if op:
        return op.id
    return None

def save_outage(db: Session, normalized: NormalizedOutage, raw_data_dict: dict):
    """
    Save or update an outage.
    Implements basic deduplication/upsert logic.
    """
    operator_id = get_operator_id(db, normalized.operator.value)
    if not operator_id:
        return None
        
    # Create RawData entry
    raw_entry = RawData(
        operator=normalized.operator.value,
        source_url=normalized.source_url,
        data=raw_data_dict
    )
    db.add(raw_entry)
    db.flush() # Get ID
    
    # Look up Region
    region_id = None
    lookup_text = f"{normalized.title.get('sv', '')} {normalized.location or ''}"
    county_name = extract_region_from_text(lookup_text, SWEDISH_COUNTIES)
    
    if county_name:
        normalized.location = county_name
        region = db.query(Region).filter(Region.name["sv"].as_string() == county_name).first()
        if region:
            region_id = region.id
            
    # Check if outage already exists
    existing = None
    if normalized.incident_id:
        existing = db.query(Outage).filter(
            Outage.operator_id == operator_id,
            Outage.incident_id == normalized.incident_id
        ).first()
        
    affected_services_json = [s.value for s in normalized.affected_services]
    
    if existing:
        # Status Change Detection
        if existing.status != normalized.status:
            print(f"INFO: Outage {existing.incident_id} changed status from {existing.status} to {normalized.status}")
        
        # Update existing
        existing.status = normalized.status
        existing.severity = normalized.severity
        existing.title = normalized.title
        existing.description = normalized.description
        existing.location = normalized.location
        existing.estimated_fix_time = normalized.estimated_fix_time
        # end_time = actual resolution time, only set when outage is resolved.
        # Clear any stale end_time that was set by the old bug (end_time = estimated_fix_time)
        # so auto_resolve_expired_outages() doesn't fight with live portal data.
        if normalized.status and normalized.status.value == 'resolved':
            if not existing.end_time:
                existing.end_time = datetime.now(timezone.utc)
        else:
            existing.end_time = None
        existing.updated_at = datetime.now(timezone.utc)
        existing.raw_data_id = raw_entry.id
        existing.affected_services = affected_services_json
        existing.region_id = region_id # Update region if detected
        existing.latitude = normalized.latitude
        existing.longitude = normalized.longitude
        return existing
    else:
        # Create new
        new_outage = Outage(
            incident_id=normalized.incident_id,
            operator_id=operator_id,
            region_id=region_id,
            raw_data_id=raw_entry.id,
            title=normalized.title,
            description=normalized.description,
            status=normalized.status,
            severity=normalized.severity,
            start_time=normalized.started_at if normalized.started_at else datetime.now(timezone.utc),
            estimated_fix_time=normalized.estimated_fix_time,
            location=normalized.location,
            latitude=normalized.latitude,
            longitude=normalized.longitude,
            affected_services=affected_services_json,
        )
        db.add(new_outage)
        return new_outage

def resolve_missing_outages(db: Session, operator_enum, seen_incident_ids: list) -> int:
    """
    Delta-based resolve: mark active outages not seen in the latest scrape as resolved.
    Used when an operator removes an incident from their portal once fixed.
    """
    operator_id = get_operator_id(db, operator_enum.value)
    if not operator_id:
        return 0

    now = datetime.now(timezone.utc)
    missing = db.query(Outage).filter(
        Outage.operator_id == operator_id,
        Outage.status != 'resolved',
        ~Outage.incident_id.in_(seen_incident_ids)
    ).all()

    for outage in missing:
        outage.status = 'resolved'
        outage.end_time = now
        outage.updated_at = now

    if missing:
        db.commit()

    return len(missing)


def auto_resolve_expired_outages(db: Session):
    """
    Find outages that are still active/scheduled but their end dates/ETAs have passed.
    Mark them as 'resolved' in the database.
    """
    now = datetime.now(timezone.utc)
    
    # Grace period: only auto-resolve outages whose ETA passed >24 hours ago.
    grace_cutoff = now - timedelta(hours=24)

    # Scraper staleness threshold: skip outages updated within the last 2 hours.
    # If a scraper just touched an outage (updated_at is fresh), the portal is
    # still actively reporting it — trust the portal, not the stale ETA.
    # Only auto-resolve outages the scraper hasn't seen in >2 hours (zombie outages).
    scraper_active_cutoff = now - timedelta(hours=2)

    # Outages still shown by a live scraper (updated recently) must NOT be auto-resolved;
    # resolve_missing_outages() will handle them once the portal removes them.
    expired_eta = db.query(Outage).filter(
        Outage.status != 'resolved',
        Outage.estimated_fix_time != None,
        Outage.estimated_fix_time <= grace_cutoff,
        Outage.updated_at <= scraper_active_cutoff,
    ).all()
    
    total_resolved = 0
    for outage in expired_eta:
        outage.status = 'resolved'
        outage.end_time = now
        outage.updated_at = now
        total_resolved += 1
        
    if total_resolved > 0:
        db.commit()
        print(f"AUTO-RESOLVE: Marked {total_resolved} expired outages as 'resolved'.")
    
    return total_resolved

def enrich_missing_geodata(db: Session) -> int:
    """
    Enrichment pass: for records that have a location name but missing lat/lon,
    attempt geocoding again. Runs after every scraper cycle.
    """
    from scrapers.common.geocoding import get_county_coordinates
    from scrapers.common.translation import SWEDISH_COUNTIES
    from scrapers.common.engine import extract_region_from_text

    SKIP_LOCATIONS = {None, '', 'Unknown', 'Sverige', 'Sweden'}

    candidates = db.query(Outage).filter(
        Outage.latitude == None,
        Outage.location != None,
        Outage.location != '',
        Outage.location != 'Unknown',
    ).all()

    enriched = 0
    now = datetime.now(timezone.utc)

    for outage in candidates:
        loc = outage.location or ''

        # Try direct county lookup first
        coords = get_county_coordinates(loc, jitter=True)

        # If not found, try extracting county from location string
        if not coords:
            county = extract_region_from_text(loc, SWEDISH_COUNTIES)
            if county:
                outage.location = county
                coords = get_county_coordinates(county, jitter=True)

        if coords:
            outage.latitude, outage.longitude = coords
            outage.updated_at = now
            enriched += 1

    if enriched:
        db.commit()

    return enriched


def enrich_region_ids(db: Session) -> int:
    """
    Fill region_id for outages that have a location name but no region_id.
    Matches outage.location against regions.name (sv field).
    """
    import json as _json
    from scrapers.db.models import Region

    regions = db.query(Region).all()
    region_map = {}
    for r in regions:
        try:
            sv = _json.loads(r.name).get('sv', '').lower()
            if sv:
                region_map[sv] = r.id
        except Exception:
            region_map[str(r.name).lower()] = r.id

    candidates = db.query(Outage).filter(
        Outage.region_id == None,
        Outage.location != None,
        Outage.location != '',
    ).all()

    now = datetime.now(timezone.utc)
    filled = 0
    for outage in candidates:
        key = (outage.location or '').lower()
        rid = region_map.get(key)
        if rid:
            outage.region_id = rid
            outage.updated_at = now
            filled += 1

    if filled:
        db.commit()
    return filled


def enrich_place_codes(db: Session) -> int:
    """
    Fill place (Plus Code / Open Location Code) from lat/lon for records missing it.
    """
    from openlocationcode import openlocationcode as olc

    candidates = db.query(Outage).filter(
        Outage.place == None,
        Outage.latitude != None,
        Outage.longitude != None,
    ).all()

    now = datetime.now(timezone.utc)
    filled = 0
    for outage in candidates:
        try:
            code = olc.encode(float(outage.latitude), float(outage.longitude), codeLength=10)
            outage.place = code
            outage.updated_at = now
            filled += 1
        except Exception:
            pass

    if filled:
        db.commit()
    return filled


def cleanup_old_data(db: Session, days: int = 30):
    """
    Remove resolved outages and raw data older than X days.
    """
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # 1. Delete old resolved outages
    deleted_count = db.query(Outage).filter(
        Outage.status == 'resolved',
        Outage.end_time < cutoff
    ).delete()
    
    # 2. Delete old raw data (orphan or just old)
    # For simplicity, just old ones
    deleted_raw = db.query(RawData).filter(
        RawData.scraped_at < cutoff
    ).delete()
    
    db.commit()
    print(f"CLEANUP: Deleted {deleted_count} old outages and {deleted_raw} raw data records.")


def log_scraper_run(db: Session, operator: str, started_at, finished_at,
                    status: str, outages_found: int = 0, outages_resolved: int = 0,
                    retry_count: int = 0, error_message: str = None):
    run = ScraperRun(
        operator=operator,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        outages_found=outages_found,
        outages_resolved=outages_resolved,
        retry_count=retry_count,
        error_message=error_message,
    )
    db.add(run)
    db.commit()


def _run_to_dict(operator: str, run) -> dict:
    if run is None:
        return {"operator": operator, "last_run": None, "finished_at": None,
                "status": "never_run", "outages_found": 0, "outages_resolved": 0,
                "retry_count": 0, "error_message": None}
    return {
        "operator": operator,
        "last_run": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "outages_found": run.outages_found,
        "outages_resolved": run.outages_resolved,
        "retry_count": run.retry_count,
        "error_message": run.error_message,
    }


def get_scraper_health(db: Session) -> list:
    """Return the latest run result for each operator."""
    from sqlalchemy import desc
    operators = ["telia", "telenor", "tre"]
    results = []
    for op in operators:
        run = (db.query(ScraperRun)
               .filter(ScraperRun.operator == op)
               .order_by(desc(ScraperRun.started_at))
               .first())
        results.append(_run_to_dict(op, run))
    return results
