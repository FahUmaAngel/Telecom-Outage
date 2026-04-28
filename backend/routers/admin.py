from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Dict, Any, Optional, Annotated
from datetime import datetime, timezone
from ..dependencies import get_db, RoleChecker
from ..schemas import ReportResponse, OutageResponse, OutageUpdate, ResolvePlaceRequest, ResolvePlaceResponse
from scrapers.db.models import RawData, Operator, UserReport, Outage
from ..utils.geocoding import resolve_place
from ..constants import OutageStatus
import json

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(RoleChecker(["admin"]))],
)

def _safe_val(v):
    """Safely extract the value from an Enum or return as is."""
    if v is None:
        return None
    return v.value if hasattr(v, 'value') else v

def _effective_status(o: Outage):
    """Keep detail and list responses aligned when the ETA has already passed."""
    raw = _safe_val(o.status) or "active"
    if raw.lower() == "resolved":
        return raw

    end = o.end_time or o.estimated_fix_time
    if end:
        try:
            end_dt = end if isinstance(end, datetime) else datetime.fromisoformat(str(end))
            end_dt = end_dt.replace(tzinfo=None)
            if end_dt < datetime.now(timezone.utc).replace(tzinfo=None):
                return "resolved"
        except Exception:
            pass

    return raw

@router.get("/scrapers", response_model=List[Dict[str, Any]])
def get_scraper_status(db: Annotated[Session, Depends(get_db)]):
    """Get the last scrape time for each operator."""
    # Group by operator and get max(scraped_at)
    subquery = db.query(
        RawData.operator,
        func.max(RawData.scraped_at).label("last_scraped_at")
    ).group_by(RawData.operator).subquery()
    
    results = db.query(subquery).all()
    
    return [
        {"operator": r.operator, "last_scraped_at": r.last_scraped_at}
        for r in results
    ]

def _map_outage_to_response(o: Outage) -> OutageResponse:
    """Helper to map Outage model to OutageResponse schema."""
    issues = []
    if o.latitude is None or o.longitude is None:
        issues.append("missing_coords")
    if o.end_time is None:
        issues.append("missing_end_date")
        
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
        place=o.place,
        quality_issues=issues,
        updated_at=o.updated_at
    )

@router.get("/outages", response_model=List[OutageResponse])
def admin_get_outages(
    db: Annotated[Session, Depends(get_db)],
    operator: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    missing_coords: Annotated[Optional[bool], Query()] = None,
    missing_end_date: Annotated[Optional[bool], Query()] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List outages for administrative editing with pagination and search."""
    query = db.query(Outage).join(Operator)
    
    if operator:
        query = query.filter(Operator.name == operator.lower())
    if status:
        query = query.filter(Outage.status == status.lower())
    
    if missing_coords is True:
        query = query.filter((Outage.latitude == None) | (Outage.longitude == None))
    elif missing_coords is False:
        query = query.filter((Outage.latitude != None) & (Outage.longitude != None))
        
    if missing_end_date is True:
        query = query.filter(Outage.end_time == None)
    elif missing_end_date is False:
        query = query.filter(Outage.end_time != None)

    if search:
        from sqlalchemy import or_, cast, String
        q = f"%{search}%"
        query = query.filter(
            or_(
                cast(Outage.id, String).like(q),
                Outage.incident_id.ilike(q),
                Outage.location.ilike(q),
                cast(Outage.title, String).ilike(q),
            )
        )
        
    query = query.options(
        joinedload(Outage.operator),
        joinedload(Outage.region)
    ).order_by(Outage.updated_at.desc())
    
    outages = query.offset(offset).limit(limit).all()
    return [_map_outage_to_response(o) for o in outages]

@router.put("/outages/{outage_id}", response_model=OutageResponse, responses={404: {"description": "Outage not found"}})
def update_outage(
    outage_id: int, 
    update_data: OutageUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """Update an outage manually (Admin only)."""
    outage = db.query(Outage).options(joinedload(Outage.operator), joinedload(Outage.region)).filter(Outage.id == outage_id).first()
    if not outage:
        raise HTTPException(status_code=404, detail="Outage not found")
    
    # Update fields if provided
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(outage, field, value)
    
    db.commit()
    db.refresh(outage)
    
    return _map_outage_to_response(outage)

@router.post("/reports/{report_id}/verify", response_model=ReportResponse, responses={404: {"description": "Report not found"}})
def verify_report(report_id: int, db: Annotated[Session, Depends(get_db)]):
    """Verify a user report."""
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = OutageStatus.VERIFIED
    db.commit()
    db.refresh(report)
    
    return ReportResponse(
        id=report.id,
        operator_name=report.operator.name if report.operator else None,
        title=report.title,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        status=report.status,
        created_at=report.created_at
    )

@router.post("/reports/{report_id}/reject", response_model=ReportResponse, responses={404: {"description": "Report not found"}})
def reject_report(report_id: int, db: Annotated[Session, Depends(get_db)]):
    """Reject a user report."""
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = OutageStatus.REJECTED
    db.commit()
    db.refresh(report)
    
    return ReportResponse(
        id=report.id,
        operator_name=report.operator.name if report.operator else None,
        title=report.title,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        status=report.status,
        created_at=report.created_at
    )

@router.post("/resolve-place", response_model=ResolvePlaceResponse, responses={404: {"description": "Place not found"}})
def admin_resolve_place(request: ResolvePlaceRequest, db: Annotated[Session, Depends(get_db)]):
    """Resolve a place string to coordinates and Map to Region."""
    from scrapers.db.models import Region
    
    result = resolve_place(request.query)
    if not result:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # Map county/region name to database ID
    region_id = None
    county_name = result.get('county')
    
    if county_name:
        # Search in database. Region.name is a JSON field {"sv": "...", "en": "..."}
        # We try to match either sv or en name.
        # SQLite JSON search: json_extract(name, '$.sv')
        
        # Normalize county name (remove 'län' or 'county' for better matching if needed, 
        # but the user specific names include 'län')
        search_name = county_name
        
        # Exact match attempt
        db_region = db.query(Region).filter(
            (func.json_extract(Region.name, '$.sv').ilike(f"{search_name}%")) |
            (func.json_extract(Region.name, '$.en').ilike(f"{search_name}%"))
        ).first()
        
        if db_region:
            region_id = db_region.id
            # Use the official DB name for display if found
            if isinstance(db_region.name, str):
                try:
                    name_dict = json.loads(db_region.name)
                    result['display_name'] = name_dict.get('sv') or result['display_name']
                except json.JSONDecodeError:
                    pass
            elif isinstance(db_region.name, dict):
                result['display_name'] = db_region.name.get('sv') or result['display_name']

    return {
        "latitude": result['latitude'],
        "longitude": result['longitude'],
        "display_name": result['display_name'],
        "region_id": region_id
    }
