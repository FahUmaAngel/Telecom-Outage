"""
Analytics endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Annotated
from ..dependencies import get_db
from ..schemas import MTTRResponse, ReliabilityResponse, HistoricalTrendResponse, DailyTrend
from scrapers.db.models import Outage, Operator
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def _calculate_mttr_hours(outage: Outage) -> float:
    """Calculate MTTR hours for a single outage with sanity checks."""
    st = outage.start_time.replace(tzinfo=None) if outage.start_time.tzinfo else outage.start_time
    et = outage.end_time.replace(tzinfo=None) if outage.end_time.tzinfo else outage.end_time
    diff = et - st
    duration_hours = diff.total_seconds() / 3600.0
    
    # Sanity Check: Ignore negative durations or those > 1 year (data errors)
    if 0 < duration_hours <= 8760:
        return duration_hours
    return 0.0

@router.get("/mttr", response_model=List[MTTRResponse])
def get_mttr(db: Annotated[Session, Depends(get_db)]):
    """Calculate Mean Time To Recovery (MTTR) per operator."""
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        outages = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.start_time.isnot(None),
            Outage.end_time.isnot(None)
        ).all()
        
        if not outages:
            results.append(MTTRResponse(operator_name=op.name, average_mttr_hours=0.0, outage_count=0))
            continue
            
        total_hours = 0.0
        valid_count = 0
        for o in outages:
            duration = _calculate_mttr_hours(o)
            if duration > 0:
                total_hours += duration
                valid_count += 1
            
        avg_hours = (total_hours / valid_count) if valid_count > 0 else 0.0
        results.append(MTTRResponse(
            operator_name=op.name,
            average_mttr_hours=round(avg_hours, 2),
            outage_count=valid_count
        ))
        
    return results

@router.get("/reliability", response_model=List[ReliabilityResponse])
def get_reliability(db: Annotated[Session, Depends(get_db)]):
    """Compare operators by reliability (outage count and total downtime)."""
    # Over the last 30 days
    since_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        outages = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.created_at >= since_date
        ).all()
        
        total_downtime = 0.0
        for o in outages:
            if o.start_time and o.end_time:
                st = o.start_time.replace(tzinfo=None) if o.start_time.tzinfo else o.start_time
                et = o.end_time.replace(tzinfo=None) if o.end_time.tzinfo else o.end_time
                diff = et - st
                total_downtime += diff.total_seconds() / 3600.0
            # If still active, maybe count downtime up to now? 
            # For simplicity, we only count resolved for downtime, but all for count.
            
        results.append(ReliabilityResponse(
            operator_name=op.name,
            outage_count=len(outages),
            total_downtime_hours=round(total_downtime, 2)
        ))
        
    return results

@router.get("/history", response_model=HistoricalTrendResponse)
def get_historical_trend(db: Annotated[Session, Depends(get_db)], days: int = 30):
    """Get aggregated outage counts per day for the last X days."""
    since_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    
    # Query all outages created in the last X days
    outages = db.query(Outage).filter(Outage.created_at >= since_date).all()
    
    # Simple aggregation in memory for SQLite compatibility and ease of logic
    counts_by_date = {}
    
    # Initialize all dates in range with 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for i in range(days + 1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        counts_by_date[d] = 0
        
    for o in outages:
        d = o.created_at.strftime("%Y-%m-%d")
        if d in counts_by_date:
            counts_by_date[d] += 1
            
    # Sort by date
    sorted_trend = [
        DailyTrend(date=d, count=c) 
        for d, c in sorted(counts_by_date.items())
    ]
    
    return {
        "total_count": len(outages),
        "trend": sorted_trend
    }

def _filter_by_service(outages: List[Outage], service: str) -> List[Outage]:
    """Filter outages by service name within affected_services JSON."""
    s_lower = service.lower()
    return [
        o for o in outages 
        if o.affected_services and any(s_lower in str(s).lower() for s in o.affected_services)
    ]


def _build_outage_key(o: Outage) -> tuple:
    return (
        str(o.title) if o.title else "",
        str(o.description) if o.description else "",
        str(o.location) if o.location else "",
        o.start_time.isoformat() if o.start_time else "",
        o.end_time.isoformat() if o.end_time else "",
    )

def _merge_affected_services(existing: Outage, incoming: Outage) -> None:
    if not incoming.affected_services:
        return
    if not existing.affected_services:
        existing.affected_services = incoming.affected_services
    else:
        existing.affected_services = list(
            set(existing.affected_services) | set(incoming.affected_services)
        )

def _get_unique_outages(outages: List[Outage]) -> List[Outage]:
    """Deduplicate outages based on title, description, location, and time."""
    unique_outages_map: dict = {}
    for o in outages:
        if not o.start_time or not o.end_time:
            continue
        key = _build_outage_key(o)
        if key not in unique_outages_map:
            unique_outages_map[key] = o
        else:
            _merge_affected_services(unique_outages_map[key], o)
    return list(unique_outages_map.values())

def _calculate_avg_mttr(outages: List[Outage]) -> float:
    """Calculate average MTTR in hours for a list of outages."""
    if not outages:
        return 0.0
    total_hours = 0.0
    valid_count = 0
    for o in outages:
        resolved_at = o.end_time
        if not resolved_at:
            continue
            
        st = o.start_time.replace(tzinfo=None) if o.start_time.tzinfo else o.start_time
        res = resolved_at.replace(tzinfo=None) if resolved_at.tzinfo else resolved_at
        
        diff = res - st
        duration_hours = diff.total_seconds() / 3600.0
        
        # Sanity check: 0 < duration < 1 year
        if 0 < duration_hours < 8760:
            total_hours += duration_hours
            valid_count += 1
            
    return total_hours / valid_count if valid_count > 0 else 0.0

@router.get("/mttr-dynamic", response_model=List[MTTRResponse])
def get_dynamic_mttr(
    db: Annotated[Session, Depends(get_db)],
    days: int = 365, 
    location: Optional[str] = None, 
    service: Optional[str] = None
):
    """Refined MTTR calculation with deduplication and granular filters."""
    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        # 1. Base Query - Use func.datetime() for robust SQLite date comparison
        query = db.query(Outage).filter(
            Outage.operator_id == op.id,
            func.datetime(Outage.start_time) >= func.datetime(since_date)
        )
        if location:
            query = query.filter(Outage.location.ilike(f"%{location}%"))
            
        outages = query.all()
        
        # 2. Filter by Service
        if service:
            outages = _filter_by_service(outages, service)
            
        # 4. Deduplicate
        outages = _get_unique_outages(outages)

        # 5. Calculate and append
        avg_h = _calculate_avg_mttr(outages)
        results.append(MTTRResponse(
            operator_name=op.name.upper(),
            average_mttr_hours=round(avg_h, 2),
            outage_count=len(outages)
        ))
        
    return results

import re

@router.get("/locations", response_model=List[str])
def get_locations(
    db: Annotated[Session, Depends(get_db)],
    operator_id: Optional[int] = None
):
    """Get unique locations from the outages table that have valid MTTR data."""
    query = db.query(Outage.location).filter(
        Outage.location.isnot(None),
        func.trim(Outage.location) != "",
        Outage.end_time.isnot(None)
    ).distinct()
    
    if operator_id:
        query = query.filter(Outage.operator_id == operator_id)
    
    results = query.order_by(Outage.location).all()
    
    # Post-process to remove bad data
    banned_exact = {"unknown", "sverige", "hela sverige", "sharper of sweden"}
    has_numbers = re.compile(r'\d')
    
    final_locations = []
    for r in results:
        loc = r[0]
        if not loc or not loc.strip():
            continue
            
        loc_clean = loc.strip()
        loc_lower = loc_clean.lower()
        
        if loc_lower in banned_exact:
            continue
            
        if has_numbers.search(loc_clean):
            continue
            
        final_locations.append(loc_clean)
        
    return final_locations

