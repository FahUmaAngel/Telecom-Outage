"""
Database CRUD operations.
"""
from sqlalchemy.orm import Session
from typing import Optional
from .models import Outage, RawData, Operator, Region
from ..common.models import NormalizedOutage, OperatorEnum
from ..common.translation import SWEDISH_COUNTIES
from ..common.engine import extract_region_from_text
from datetime import datetime, timezone
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

    # Check if outage already exists
    existing = None
    if normalized.incident_id:
        existing = db.query(Outage).filter(
            Outage.operator_id == operator_id,
            Outage.incident_id == normalized.incident_id
        ).first()

    # Skip scheduled outages as per user request
    if normalized.status == 'scheduled':
        if existing and existing.status != 'resolved':
            print(f"INFO: Outage {normalized.incident_id} is now scheduled. Marking as resolved.")
            existing.status = 'resolved'
            existing.end_time = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
            return existing
        
        print(f"INFO: Skipping scheduled outage {normalized.incident_id}")
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
        
        # Priority: Use end_time only if status is resolved
        if normalized.status == 'resolved':
            existing.end_time = normalized.end_time or existing.end_time or datetime.now(timezone.utc)
        else:
            existing.end_time = None
        
        # Stop using ETA as end_time or at all in normalized flow as per request
        existing.estimated_fix_time = None 
            
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
            end_time=normalized.end_time if normalized.status == 'resolved' else None,
            estimated_fix_time=None, # Stop using ETA
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
    now = datetime.now(timezone.utc)
    
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
        outage.end_time = now
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


def mark_missing_outages_resolved(db: Session, operator_name: str, current_incident_ids: list):
    """
    Mark outages as 'resolved' if they are not in the current list of incident IDs for an operator.
    """
    operator_id = get_operator_id(db, operator_name)
    if not operator_id:
        return 0

    now = datetime.now(timezone.utc)
    
    # Find active outages for this operator that are NOT in the current_incident_ids
    query = db.query(Outage).filter(
        Outage.operator_id == operator_id,
        Outage.status != 'resolved',
        ~Outage.incident_id.in_(current_incident_ids)
    )
    
    missing_outages = query.all()
    count = len(missing_outages)
    
    if count > 0:
        for outage in missing_outages:
            outage.status = 'resolved'
            outage.end_time = now
            outage.updated_at = now
        db.commit()
        print(f"SYNC: Marked {count} missing {operator_name} outages as 'resolved'.")
    
    return count
