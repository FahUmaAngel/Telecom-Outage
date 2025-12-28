from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage
db = SessionLocal()
try:
    total = db.query(Outage).count()
    resolved = db.query(Outage).filter(Outage.status == 'resolved').count()
    resolved_with_times = db.query(Outage).filter(
        Outage.status == 'resolved', 
        Outage.start_time.isnot(None), 
        Outage.end_time.isnot(None)
    ).count()
    active = db.query(Outage).filter(Outage.status == 'active').count()
    
    print(f"Total: {total}")
    print(f"Resolved: {resolved}")
    print(f"Resolved with times: {resolved_with_times}")
    print(f"Active: {active}")
    
    if resolved_with_times > 0:
        sample = db.query(Outage).filter(
            Outage.status == 'resolved', 
            Outage.start_time.isnot(None), 
            Outage.end_time.isnot(None)
        ).first()
        diff = sample.end_time - sample.start_time
        print(f"Sample resolution time: {diff.total_seconds()} seconds")
finally:
    db.close()
