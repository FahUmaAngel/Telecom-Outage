"""
Operator endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_db
from ..schemas import OperatorResponse
from scrapers.db.models import Operator

router = APIRouter(prefix="/api/v1/operators", tags=["operators"])

@router.get("/", response_model=List[OperatorResponse])
def get_operators(db: Session = Depends(get_db)):
    """List all supported operators."""
    operators = db.query(Operator).all()
    # Map SQLAlchemy model to Pydantic
    return [
        OperatorResponse(id=op.id, name=op.name)
        for op in operators
    ]
