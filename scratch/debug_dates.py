import sys
import os
sys.path.append(os.getcwd())

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage

db = SessionLocal()
resolved_no_end = db.query(Outage).filter(Outage.status == 'resolved', Outage.end_time == None).all()
print(f"Resolved outages with no end_time: {len(resolved_no_end)}")

for o in resolved_no_end[:10]:
    print(f"ID: {o.id}, Incident ID: {o.incident_id}, Updated At: {o.updated_at}, Estimated Fix: {o.estimated_fix_time}")

db.close()
