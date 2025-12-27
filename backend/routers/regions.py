from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..dependencies import get_db
from .. import schemas
from scrapers.db.models import Region, Outage

router = APIRouter(
    prefix="/regions",
    tags=["Regions"]
)

@router.get("/", response_model=List[schemas.RegionResponse])
def get_regions(db: Session = Depends(get_db)):
    """
    Get all regions with their current active outage counts.
    """
    # Query regions and join with outages to count active ones
    results = db.query(
        Region,
        func.count(Outage.id).label("outage_count")
    ).outerjoin(
        Outage, 
        (Outage.region_id == Region.id) & (Outage.status != 'resolved')
    ).group_by(Region.id).all()
    
    regions = []
    for region, count in results:
        regions.append(schemas.RegionResponse(
            id=region.id,
            name=region.name,
            outage_count=count
        ))
        
    return regions

@router.get("/{id}", response_model=schemas.RegionResponse)
def get_region(id: int, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.id == id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
        
    active_count = db.query(func.count(Outage.id)).filter(
        Outage.region_id == id,
        Outage.status != 'resolved'
    ).scalar()
    
    return schemas.RegionResponse(
        id=region.id,
        name=region.name,
        outage_count=active_count
    )
