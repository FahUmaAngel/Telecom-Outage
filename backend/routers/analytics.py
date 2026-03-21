"""
Analytics endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..dependencies import get_db
from ..schemas import MTTRResponse, ReliabilityResponse, HistoricalTrendResponse, DailyTrend
from scrapers.db.models import Outage, Operator
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/mttr", response_model=List[MTTRResponse])
def get_mttr(db: Session = Depends(get_db)):
    """Calculate Mean Time To Recovery (MTTR) per operator."""
    # SQLite logic: average(time_diff)
    # We filter only resolved outages (where end_time and start_time are present)
    
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        # Fetch outages for this operator that have both start and end times
        outages = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.start_time.isnot(None),
            Outage.end_time.isnot(None)
        ).all()
        
        if not outages:
            results.append(MTTRResponse(operator_name=op.name, average_mttr_hours=0.0, outage_count=0))
            continue
            
        total_hours = 0.0
        valid_outages = 0
        for o in outages:
            st = o.start_time.replace(tzinfo=None) if o.start_time.tzinfo else o.start_time
            et = o.end_time.replace(tzinfo=None) if o.end_time.tzinfo else o.end_time
            diff = et - st
            duration_hours = diff.total_seconds() / 3600.0
            
            # Sanity Check: Ignore negative durations or those > 1 year (data errors)
            if duration_hours <= 0 or duration_hours > 8760:
                continue
                
            total_hours += duration_hours
            valid_outages += 1
            
        if valid_outages == 0:
            results.append(MTTRResponse(operator_name=op.name, average_mttr_hours=0.0, outage_count=0))
            continue
            
        avg_hours = total_hours / valid_outages
        results.append(MTTRResponse(
            operator_name=op.name,
            average_mttr_hours=round(avg_hours, 2),
            outage_count=valid_outages
        ))
        
    return results

@router.get("/reliability", response_model=List[ReliabilityResponse])
def get_reliability(db: Session = Depends(get_db)):
    """Compare operators by reliability (outage count and total downtime)."""
    # Over the last 30 days
    since_date = datetime.utcnow() - timedelta(days=30)
    
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
def get_historical_trend(db: Session = Depends(get_db), days: int = 30):
    """Get aggregated outage counts per day for the last X days."""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Query all outages created in the last X days
    outages = db.query(Outage).filter(Outage.created_at >= since_date).all()
    
    # Simple aggregation in memory for SQLite compatibility and ease of logic
    counts_by_date = {}
    
    # Initialize all dates in range with 0
    for i in range(days + 1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
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

@router.get("/mttr-dynamic", response_model=List[MTTRResponse])
def get_dynamic_mttr(
    days: int = 365, 
    location: Optional[str] = None, 
    location_type: Optional[str] = None,
    service: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Refined MTTR calculation with deduplication and granular filters."""
    since_date = datetime.utcnow() - timedelta(days=days)
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        # Initial query for recent outages
        query = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.start_time >= since_date
        )
        
        # Location name filtering
        if location:
            query = query.filter(Outage.location.ilike(f"%{location}%"))
            
        outages = query.all()
        
        # Service filtering (since affected_services is JSON list)
        if service:
            filtered_outages = []
            s_lower = service.lower()
            for o in outages:
                services = o.affected_services or []
                if any(s_lower in str(s).lower() for s in services):
                    filtered_outages.append(o)
            outages = filtered_outages
            
        # Location type filtering (Län vs City)
        if location_type:
            lt_lower = location_type.lower()
            filtered_by_type = []
            for o in outages:
                if not o.location:
                    continue
                is_lan = o.location.lower().endswith("län")
                if lt_lower == "lan" and is_lan:
                    filtered_by_type.append(o)
                elif lt_lower == "city" and not is_lan:
                    filtered_by_type.append(o)
            outages = filtered_by_type
            
        # Deduplication (handled by prioritized resolution time)
        unique_outages = []
        seen = set()
        for o in outages:
            # Must have start_time AND at least one resolution timestamp
            if not o.start_time or (not o.end_time and not o.estimated_fix_time):
                continue
                
            # Use end_time if present, otherwise estimated_fix_time
            resolved_dt = o.end_time or o.estimated_fix_time
            resolved_str = resolved_dt.isoformat() if resolved_dt else ""
            
            key = (title_str, desc_str, loc_str, start_str, resolved_str)
            if key not in seen:
                seen.add(key)
                unique_outages.append(o)
        
        outages = unique_outages

        if not outages:
            results.append(MTTRResponse(operator_name=op.name.upper(), average_mttr_hours=0.0, outage_count=0))
            continue
            
        total_hours = 0.0
        for o in outages:
            # Priority: end_time > estimated_fix_time
            resolved_at = o.end_time or o.estimated_fix_time
            
            st = o.start_time.replace(tzinfo=None) if o.start_time.tzinfo else o.start_time
            res = resolved_at.replace(tzinfo=None) if resolved_at.tzinfo else resolved_at
            
            diff = res - st
            duration_hours = diff.total_seconds() / 3600.0
            
            # Simple sanity check
            if duration_hours > 0 and duration_hours < 8760:
                total_hours += duration_hours
            
        avg_mttr = total_hours / len(outages)
        results.append(MTTRResponse(
            operator_name=op.name.upper(),
            average_mttr_hours=round(avg_mttr, 2),
            outage_count=len(outages)
        ))
        
    return results

@router.get("/locations", response_model=List[str])
def get_locations(operator_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get unique locations from the outages table."""
    query = db.query(Outage.location).distinct()
    if operator_id:
        query = query.filter(Outage.operator_id == operator_id)
    
    results = query.filter(Outage.location.isnot(None)).order_by(Outage.location).all()
    # Flatten the results from tuples to a single list of strings
    return [r[0] for r in results]

