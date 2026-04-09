import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator
from backend.schemas import OutageResponse
from pydantic import ValidationError

db = SessionLocal()
tre_op = db.query(Operator).filter(Operator.name == 'tre').first()
outages = db.query(Outage).filter(Outage.operator_id == tre_op.id).all()

print(f"Testing validation on {len(outages)} Tre outages...")

success = 0
for i, o in enumerate(outages):
    try:
        resp = OutageResponse(
            id=o.id,
            incident_id=o.incident_id,
            operator_id=o.operator_id,
            operator_name=o.operator.name,
            region_id=o.region_id,
            region_name=o.region.name if o.region else None,
            raw_data_id=o.raw_data_id,
            title=o.title if o.title else {},
            description=o.description,
            status=o.status,
            severity=o.severity,
            start_time=o.start_time,
            end_time=o.end_time,
            estimated_fix_time=o.estimated_fix_time,
            location=o.location,
            latitude=o.latitude,
            longitude=o.longitude,
            affected_services=o.affected_services if o.affected_services else [],
            updated_at=o.updated_at
        )
        success += 1
    except ValidationError as e:
        print(f"Validation Error on Outage ID {o.id}:")
        print(e)
        break

print(f"Successfully validated {success} out of {len(outages)}")
db.close()
