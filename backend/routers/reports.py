"""
User report endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..schemas import ReportCreate, ReportResponse, HotspotResponse
from scrapers.db.models import UserReport, Operator
from scrapers.common.crowd_engine import detect_hotspots, aggregate_external_signals

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@router.get("/hotspots", response_model=List[HotspotResponse])
def get_hotspots(db: Session = Depends(get_db)):
    """Get active crowd hotspots and external signals."""
    hotspots = detect_hotspots(db)
    external = aggregate_external_signals()
    return hotspots + external

@router.post("/", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """Submit a new outage report."""
    operator_id = None
    if report.operator_name:
        op = db.query(Operator).filter(Operator.name == report.operator_name.lower()).first()
        if op:
            operator_id = op.id
            
    new_report = UserReport(
        operator_id=operator_id,
        title=report.title,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        status="pending"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return ReportResponse(
        id=new_report.id,
        operator_name=report.operator_name if operator_id else None,
        title=new_report.title,
        description=new_report.description,
        latitude=new_report.latitude,
        longitude=new_report.longitude,
        status=new_report.status,
        created_at=new_report.created_at
    )

@router.get("/", response_model=List[ReportResponse])
def get_reports(db: Session = Depends(get_db)):
    """List all user reports."""
    reports = db.query(UserReport).all()
    return [
        ReportResponse(
            id=r.id,
            operator_name=r.operator.name if r.operator else None,
            title=r.title,
            description=r.description,
            latitude=r.latitude,
            longitude=r.longitude,
            status=r.status,
            created_at=r.created_at
        )
        for r in reports
    ]
