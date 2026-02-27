"""
Analytics endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..dependencies import get_db
from ..schemas import MTTRResponse, ReliabilityResponse, HistoricalTrendResponse, DailyTrend
from scrapers.db.models import Outage, Operator
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/mttr", response_model=List[MTTRResponse])
def get_mttr(db: Session = Depends(get_db)):
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
        for o in outages:
            diff = o.end_time - o.start_time
            total_hours += diff.total_seconds() / 3600.0
            
        avg_hours = total_hours / len(outages)
        results.append(MTTRResponse(
            operator_name=op.name,
            average_mttr_hours=round(avg_hours, 2),
            outage_count=len(outages)
        ))
        
    return results

@router.get("/mttr-dynamic")
def get_mttr_dynamic(
    days: int = 30, 
    city: str = None, 
    db: Session = Depends(get_db)
):
    """
    Detailed MTTR calculation with time range and city filtering.
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    operators = db.query(Operator).all()
    results = []
    
    for op in operators:
        # Include outages with either end_time or estimated_fix_time
        query = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.start_time.isnot(None),
            (Outage.end_time.isnot(None) | Outage.estimated_fix_time.isnot(None)),
            Outage.created_at >= since_date
        )
        
        if city and op.name.lower() == 'tre':
            query = query.filter(Outage.location == city)
        
        outages = query.all()
        
        if not outages and op.name.lower() != 'tre':
            # Placeholders for non-Tre if no data
            base_mttr = 4.2 if op.name.lower() == 'telia' else 12.5
            results.append({
                "operator_name": op.name,
                "average_mttr_hours": base_mttr,
                "outage_count": 0,
                "is_real": False
            })
            continue
        
        if not outages:
            results.append({
                "operator_name": op.name, 
                "average_mttr_hours": 0.0, 
                "outage_count": 0,
                "is_real": op.name.lower() == 'tre'
            })
            continue
            
        total_hours = 0.0
        valid_count = 0
        for o in outages:
            # Use end_time as first choice, estimated_fix_time as fallback
            finish = o.end_time or o.estimated_fix_time
            if not finish or not o.start_time:
                continue
                
            diff = finish - o.start_time
            total_hours += max(0, diff.total_seconds() / 3600.0)
            valid_count += 1
            
        if valid_count == 0:
            avg_hours = 0.0
        else:
            avg_hours = total_hours / valid_count
        
        results.append({
            "operator_name": op.name,
            "average_mttr_hours": round(avg_hours, 2),
            "outage_count": valid_count,
            "is_real": op.name.lower() == 'tre'
        })
        
    return results

@router.get("/cities")
def get_cities(db: Session = Depends(get_db)):
    """Get list of cities that have data (currently focusing on Tre)."""
    tre_op = db.query(Operator).filter(Operator.name.ilike('tre')).first()
    if not tre_op:
        return []
        
    cities = db.query(Outage.location).filter(
        Outage.operator_id == tre_op.id,
        Outage.location.isnot(None),
        Outage.location != ""
    ).distinct().all()
    
    return sorted([c[0] for c in cities])

@router.get("/reliability", response_model=List[ReliabilityResponse])
def get_reliability(db: Session = Depends(get_db)):
    """Compare operators by reliability."""
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
            finish = o.end_time or o.estimated_fix_time
            if o.start_time and finish:
                diff = finish - o.start_time
                total_downtime += max(0, diff.total_seconds() / 3600.0)
            
        results.append(ReliabilityResponse(
            operator_name=op.name,
            outage_count=len(outages),
            total_downtime_hours=round(total_downtime, 2)
        ))
        
    return results

@router.get("/history", response_model=HistoricalTrendResponse)
def get_historical_trend(db: Session = Depends(get_db), days: int = 30):
    """Get aggregated outage counts per day."""
    since_date = datetime.utcnow() - timedelta(days=days)
    outages = db.query(Outage).filter(Outage.created_at >= since_date).all()
    
    counts_by_date = {}
    for i in range(days + 1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        counts_by_date[d] = 0
        
    for o in outages:
        d = o.created_at.strftime("%Y-%m-%d")
        if d in counts_by_date:
            counts_by_date[d] += 1
            
    sorted_trend = [
        DailyTrend(date=d, count=c) 
        for d, c in sorted(counts_by_date.items())
    ]
    
    return HistoricalTrendResponse(
        total_count=len(outages),
        trend=sorted_trend
    )
