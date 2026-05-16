"""
Analytics endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Annotated
from ..dependencies import get_db
from ..schemas import MTTRResponse, ReliabilityResponse, HistoricalTrendResponse, DailyTrend
from scrapers.db.models import Outage, Operator
from datetime import datetime, timedelta, timezone
import re

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# --- Input Validation Helpers ---

DAYS_MIN = 1
DAYS_MAX = 365

def _clamp_days(days: int) -> int:
    """Sanitize user-supplied day range: clamp to [1, 365] to prevent DoS.
    
    SonarQube S6680: Never use raw user-controlled data as loop bounds.
    Always clamp/validate first before using in iteration or date arithmetic.
    """
    return max(DAYS_MIN, min(days, DAYS_MAX))

def _strip_tz(dt: datetime) -> datetime:
    """Normalize datetime to naive UTC by stripping timezone info."""
    return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt


def _calculate_mttr_hours(outage: Outage) -> float:
    """Calculate MTTR hours for a single outage with sanity checks."""
    st = _strip_tz(outage.start_time)
    et = _strip_tz(outage.end_time)
    duration_hours = (et - st).total_seconds() / 3600.0
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
    # Over the last 30 days — internal constant, not user-supplied
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
                st = _strip_tz(o.start_time)
                et = _strip_tz(o.end_time)
                total_downtime += (et - st).total_seconds() / 3600.0
            
        results.append(ReliabilityResponse(
            operator_name=op.name,
            outage_count=len(outages),
            total_downtime_hours=round(total_downtime, 2)
        ))
        
    return results


@router.get("/history", response_model=HistoricalTrendResponse)
def get_historical_trend(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=DAYS_MIN, le=DAYS_MAX, description="Number of days of history to retrieve (1-365)")
):
    """Get aggregated outage counts per day for the last X days."""
    # S6680: Clamp validated user input before using as iteration bound
    safe_days = _clamp_days(days)
    since_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    
    outages = db.query(Outage).filter(Outage.created_at >= since_date).all()
    
    # Initialize all dates in range with 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    counts_by_date = {
        (now - timedelta(days=i)).strftime("%Y-%m-%d"): 0
        for i in range(safe_days + 1)
    }
        
    for o in outages:
        d = o.created_at.strftime("%Y-%m-%d")
        if d in counts_by_date:
            counts_by_date[d] += 1
            
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
        if not o.end_time:
            continue
        st = _strip_tz(o.start_time)
        res = _strip_tz(o.end_time)
        duration_hours = (res - st).total_seconds() / 3600.0
        # Sanity check: 0 < duration < 1 year
        if 0 < duration_hours < 8760:
            total_hours += duration_hours
            valid_count += 1
    return total_hours / valid_count if valid_count > 0 else 0.0


@router.get("/mttr-dynamic", response_model=List[MTTRResponse])
def get_dynamic_mttr(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=365, ge=DAYS_MIN, le=DAYS_MAX, description="Lookback period in days (1-365)"),
    location: Optional[str] = None, 
    service: Optional[str] = None
):
    """Refined MTTR calculation with deduplication and granular filters."""
    # S6680: Clamp validated user input before using in date arithmetic
    safe_days = _clamp_days(days)
    since_date = datetime.now(timezone.utc) - timedelta(days=safe_days)
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        query = db.query(Outage).filter(
            Outage.operator_id == op.id,
            func.datetime(Outage.start_time) >= func.datetime(since_date)
        )
        if location:
            query = query.filter(Outage.location.ilike(f"%{location}%"))
            
        outages = query.all()
        
        if service:
            outages = _filter_by_service(outages, service)
            
        outages = _get_unique_outages(outages)
        avg_h = _calculate_avg_mttr(outages)
        results.append(MTTRResponse(
            operator_name=op.name.upper(),
            average_mttr_hours=round(avg_h, 2),
            outage_count=len(outages)
        ))
        
    return results



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

