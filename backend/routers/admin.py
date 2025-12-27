from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from ..dependencies import get_db
from ..schemas import ReportResponse
from scrapers.db.models import RawData, Operator, UserReport

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/scrapers", response_model=List[Dict[str, Any]])
def get_scraper_status(db: Session = Depends(get_db)):
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

@router.post("/reports/{report_id}/verify", response_model=ReportResponse)
def verify_report(report_id: int, db: Session = Depends(get_db)):
    """Verify a user report."""
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = "verified"
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

@router.post("/reports/{report_id}/reject", response_model=ReportResponse)
def reject_report(report_id: int, db: Session = Depends(get_db)):
    """Reject a user report."""
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = "rejected"
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
