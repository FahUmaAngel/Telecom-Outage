"""
Analytics endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..dependencies import get_db
from ..schemas import MTTRResponse, ReliabilityResponse
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
                diff = o.end_time - o.start_time
                total_downtime += diff.total_seconds() / 3600.0
            # If still active, maybe count downtime up to now? 
            # For simplicity, we only count resolved for downtime, but all for count.
            
        results.append(ReliabilityResponse(
            operator_name=op.name,
            outage_count=len(outages),
            total_downtime_hours=round(total_downtime, 2)
        ))
        
    return results
