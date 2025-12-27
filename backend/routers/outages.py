"""
Outage endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..dependencies import get_db
from ..schemas import OutageResponse, OutageStatus
from scrapers.db.models import Outage, Operator, Region
import math
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/outages", tags=["outages"])

@router.get("/history", response_model=List[OutageResponse])
def get_outage_history(
    db: Session = Depends(get_db),
    operator: Optional[str] = None,
    days: int = 7
):
    """
    Get resolved outages history.
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    query = db.query(Outage).join(Operator).filter(
        Outage.status == "resolved",
        Outage.end_time >= since_date
    )
    
    if operator:
        query = query.filter(Operator.name == operator.lower())
        
    outages = query.all()
    
    return [
        OutageResponse(
            id=o.id,
            incident_id=o.incident_id,
            operator_name=o.operator.name,
            title=o.title if o.title else {},
            description=o.description,
            status=o.status.value if o.status else "unknown",
            severity=o.severity.value if o.severity else "unknown",
            start_time=o.start_time,
            end_time=o.end_time,
            estimated_fix_time=o.estimated_fix_time,
            location=o.location,
            latitude=o.latitude,
            longitude=o.longitude,
            affected_services=o.affected_services if o.affected_services else [],
            updated_at=o.updated_at,
            region_id=o.region_id,
            region_name=o.region.name if o.region else None
        )
        for o in outages
    ]

@router.get("/", response_model=List[OutageResponse])
def get_outages(
    db: Session = Depends(get_db),
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
    
    # 1. Basic Filtering
    if operator:
        query = query.filter(Operator.name == operator.lower())
    
    if status:
        query = query.filter(Outage.status == status)
        
    # Execute query first, then filter geospatial in Python (SQLite limitation)
    outages = query.all()
    
    results = []
    
    # 2. Geospatial Filtering (Haversine)
    if lat is not None and lon is not None:
        for outage in outages:
            # Skip if outage has no location
            if outage.latitude is None or outage.longitude is None:
                continue
                
            dist = haversine(lat, lon, outage.latitude, outage.longitude)
            if dist <= radius_km:
                results.append(outage)
    else:
        results = outages
        
    # Convert to Response Model
    response_list = []
    for o in results:
        response_list.append(OutageResponse(
            id=o.id,
            incident_id=o.incident_id,
            operator_name=o.operator.name,
            title=o.title if o.title else {},
            description=o.description,
            status=o.status.value if o.status else "unknown",
            severity=o.severity.value if o.severity else "unknown",
            start_time=o.start_time,
            end_time=o.end_time,
            estimated_fix_time=o.estimated_fix_time,
            location=o.location,
            latitude=o.latitude,
            longitude=o.longitude,
            affected_services=o.affected_services if o.affected_services else [],
            updated_at=o.updated_at,
            region_id=o.region_id,
            region_name=o.region.name if o.region else None
        ))
        
    return response_list

@router.get("/{outage_id}", response_model=OutageResponse)
def get_outage_detail(outage_id: int, db: Session = Depends(get_db)):
    outage = db.query(Outage).filter(Outage.id == outage_id).first()
    if not outage:
        raise HTTPException(status_code=404, detail="Outage not found")
        
    return OutageResponse(
            id=outage.id,
            incident_id=outage.incident_id,
            operator_name=outage.operator.name,
            title=outage.title if outage.title else {},
            description=outage.description,
            status=outage.status.value if outage.status else "unknown",
            severity=outage.severity.value if outage.severity else "unknown",
            start_time=outage.start_time,
            end_time=outage.end_time,
            estimated_fix_time=outage.estimated_fix_time,
            location=outage.location,
            latitude=outage.latitude,
            longitude=outage.longitude,
            affected_services=outage.affected_services if outage.affected_services else [],
            updated_at=outage.updated_at,
            region_id=outage.region_id,
            region_name=outage.region.name if outage.region else None
        )

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
