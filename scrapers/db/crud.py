"""
Database CRUD operations.
"""
from sqlalchemy.orm import Session
from .models import Outage, RawData, Operator, Region
from ..common.models import NormalizedOutage, OperatorEnum
from ..common.translation import SWEDISH_COUNTIES
from ..common.engine import extract_region_from_text
from datetime import datetime
import json

from sqlalchemy import func

def get_operator_id(db: Session, operator_name: str) -> int:
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
        existing.end_time = normalized.estimated_fix_time
        existing.updated_at = datetime.utcnow()
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
            start_time=normalized.started_at if normalized.started_at else datetime.utcnow(),
            estimated_fix_time=normalized.estimated_fix_time,
            location=normalized.location,
            latitude=normalized.latitude,
            longitude=normalized.longitude,
            affected_services=affected_services_json,
        )
        db.add(new_outage)
        return new_outage

def auto_resolve_expired_outages(db: Session):
    """
    Find outages that are still active/scheduled but their end dates/ETAs have passed.
    Mark them as 'resolved' in the database.
    """
    now = datetime.utcnow()
    
    # 1. Check end_time (definite resolution time)
    expired_end = db.query(Outage).filter(
        Outage.status != 'resolved',
        Outage.end_time != None,
        Outage.end_time <= now
    ).all()
    
    # 2. Check estimated_fix_time (ETA passed)
    # We only auto-resolve based on ETA if there's no definite end_time
    expired_eta = db.query(Outage).filter(
        Outage.status != 'resolved',
        Outage.end_time == None,
        Outage.estimated_fix_time != None,
        Outage.estimated_fix_time <= now
    ).all()
    
    total_resolved = 0
    for outage in expired_end + expired_eta:
        outage.status = 'resolved'
        outage.updated_at = now
        total_resolved += 1
        
    if total_resolved > 0:
        db.commit()
        print(f"AUTO-RESOLVE: Marked {total_resolved} expired outages as 'resolved'.")
    
    return total_resolved

def cleanup_old_data(db: Session, days: int = 30):
    """
    Remove resolved outages and raw data older than X days.
    """
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
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
