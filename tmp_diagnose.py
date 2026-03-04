
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.schemas import OutageResponse
from scrapers.db.models import Outage, Operator

def _safe_val(v):
    if v is None:
        return None
    return v.value if hasattr(v, 'value') else v

def diagnose():
    db = next(get_db())
    outages = db.query(Outage).join(Operator).all()
    print(f"Total outages found: {len(outages)}")
    
    operators = set(o.operator.name for o in outages)
    print(f"Operators: {operators}")
    
    failures = []
    success_count = 0
    
    for o in outages:
        try:
            OutageResponse(
                id=o.id,
                incident_id=o.incident_id,
                operator_id=o.operator_id,
                operator_name=o.operator.name,
                region_id=o.region_id,
                region_name=o.region.name if o.region else None,
                raw_data_id=o.raw_data_id,
                title=o.title if o.title else {},
                description=o.description,
                status=_safe_val(o.status),
                severity=_safe_val(o.severity),
                start_time=o.start_time,
                end_time=o.end_time,
                estimated_fix_time=o.estimated_fix_time,
                location=o.location,
                latitude=o.latitude,
                longitude=o.longitude,
                affected_services=o.affected_services if o.affected_services else [],
                updated_at=o.updated_at
            )
            success_count += 1
        except Exception as e:
            failures.append({
                "id": o.id,
                "operator": o.operator.name,
                "error": str(e)
            })
            if len(failures) >= 10:
                break
                
    print(f"Success: {success_count}")
    print(f"Failures: {len(failures)}")
    for f in failures:
        print(f"Failure ID {f['id']} ({f['operator']}): {f['error']}")

if __name__ == "__main__":
    diagnose()
