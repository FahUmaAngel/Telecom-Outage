
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.schemas import OutageResponse
from scrapers.db.models import Outage, Operator

def diagnose():
    db = next(get_db())
    outages = db.query(Outage).all()
    print(f"Total outages found: {len(outages)}")
    
    statuses = set()
    severities = set()
    
    for o in outages:
        s = o.status
        if hasattr(s, 'value'): s = s.value
        statuses.add(s)
        
        sev = o.severity
        if hasattr(sev, 'value'): sev = sev.value
        severities.add(sev)
        
    print(f"Unique Statuses in DB: {statuses}")
    print(f"Unique Severities in DB: {severities}")

if __name__ == "__main__":
    diagnose()
