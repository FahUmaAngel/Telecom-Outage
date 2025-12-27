"""
Database CRUD operations.
"""
from sqlalchemy.orm import Session
from .models import Outage, RawData, Operator
from ..common.models import NormalizedOutage, OperatorEnum
from datetime import datetime
import json

def get_operator_id(db: Session, operator_name: str) -> int:
    op = db.query(Operator).filter(Operator.name == operator_name).first()
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
    
    # Check if outage already exists (by incident_id or similar)
    # Using incident_id if available, otherwise might need other logic
    existing = None
    if normalized.incident_id:
        existing = db.query(Outage).filter(
            Outage.operator_id == operator_id,
            Outage.incident_id == normalized.incident_id
        ).first()
    
    # If not found by ID, maybe check by Title + StartTime + Operator?
    # For now relying on incident_id which we generate in mapper if missing
    
    affected_services_json = [s.value for s in normalized.affected_services]
    
    if existing:
        # Update existing
        existing.status = normalized.status
        existing.severity = normalized.severity
        existing.title = normalized.title # Update bilingual title
        existing.description = normalized.description
        existing.end_time = normalized.estimated_fix_time # Updating est fix time
        existing.updated_at = datetime.utcnow()
        existing.raw_data_id = raw_entry.id # Link to newest raw data
        existing.affected_services = affected_services_json
        # Only update start_time if it was null? usually start_time shouldn't change
        # existing.start_time = normalized.started_at 
        return existing
    else:
        # Create new
        new_outage = Outage(
            incident_id=normalized.incident_id,
            operator_id=operator_id,
            raw_data_id=raw_entry.id,
            title=normalized.title,
            description=normalized.description,
            status=normalized.status,
            severity=normalized.severity,
            start_time=normalized.started_at,
            estimated_fix_time=normalized.estimated_fix_time,
            location=normalized.location,
            affected_services=affected_services_json,
            # geom=... # If we had lat/lon
        )
        db.add(new_outage)
        return new_outage
