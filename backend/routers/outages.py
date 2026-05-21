"""
Outage endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Annotated
from ..dependencies import get_db
from ..schemas import OutageResponse, OutageStatus
from scrapers.db.models import Outage, Operator, Region
import math
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/outages", tags=["outages"])

def _safe_val(v):
    """Safely extract the value from an Enum or return as is."""
    if v is None:
        return None
    return v.value if hasattr(v, 'value') else v

def _effective_status(o):
    """Return the status stored in the database without overriding by ETA."""
    return _safe_val(o.status) or 'active'

def _map_to_outage_response(o: Outage) -> OutageResponse:
    """Helper to map SQLAlchemy Outage model to Pydantic OutageResponse."""
    return OutageResponse(
        id=o.id,
        incident_id=o.incident_id,
        operator_id=o.operator_id,
        operator_name=o.operator.name,
        region_id=o.region_id,
        region_name=o.region.name if o.region else None,
        raw_data_id=o.raw_data_id,
        title=o.title if o.title else {},
        description=o.description,
        status=_effective_status(o),
        severity=_safe_val(o.severity),
        start_time=o.start_time,
        end_time=o.end_time,
        estimated_fix_time=o.estimated_fix_time,
        location=o.location,
        latitude=o.latitude,
        longitude=o.longitude,
        affected_services=o.affected_services if o.affected_services else [],
        updated_at=o.updated_at
    )

@router.get("/history", response_model=List[OutageResponse])
def get_outage_history(
    db: Annotated[Session, Depends(get_db)],
    operator: Optional[str] = None,
    days: int = 7
):
    """
    Get resolved outages history.
    """
    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    query = db.query(Outage).join(Operator).filter(
        Outage.status == "resolved",
        Outage.end_time >= since_date
    )
    
    if operator:
        query = query.filter(Operator.name == operator.lower())
        
    outages = query.options(joinedload(Outage.operator), joinedload(Outage.region)).all()
    
    return [_map_to_outage_response(o) for o in outages]

@router.get("", response_model=List[OutageResponse])
def get_outages(
    db: Annotated[Session, Depends(get_db)],
    operator: Optional[str] = None,
    status: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: float = 10.0
):
    """
    Get outages with optional filtering and geospatial search.
    """
    query = db.query(Outage).join(Operator)
    
    if operator:
        query = query.filter(Operator.name == operator.lower())
    
    if status:
        query = query.filter(Outage.status == status)
        
    outages = query.options(joinedload(Outage.operator), joinedload(Outage.region)).all()
    
    results = []
    if lat is not None and lon is not None:
        for outage in outages:
            if outage.latitude is None or outage.longitude is None:
                continue
            dist = haversine(lat, lon, outage.latitude, outage.longitude)
            if dist <= radius_km:
                results.append(outage)
    else:
        results = outages
        
    return [_map_to_outage_response(o) for o in results]

@router.get("/{outage_id}", response_model=OutageResponse, responses={404: {"description": "Outage not found"}})
def get_outage_detail(outage_id: int, db: Annotated[Session, Depends(get_db)]):
    outage = db.query(Outage).options(joinedload(Outage.operator), joinedload(Outage.region)).filter(Outage.id == outage_id).first()
    if not outage:
        raise HTTPException(status_code=404, detail="Outage not found")
        
    return _map_to_outage_response(outage)

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Result in Kilometers
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r
