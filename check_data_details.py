from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage
db = SessionLocal()
try:
    outages = db.query(Outage).all()
    has_start = [o for o in outages if o.start_time]
    has_end = [o for o in outages if o.end_time]
    active = [o for o in outages if o.status == 'active']
    resolved = [o for o in outages if o.status == 'resolved']
    
    print(f"Total: {len(outages)}")
    print(f"Active: {len(active)}")
    print(f"Resolved: {len(resolved)}")
    print(f"Has Start Time: {len(has_start)}")
    print(f"Has End Time: {len(has_end)}")
    
    if len(has_start) > 0:
        op_counts = {}
        for o in has_start:
            op_name = o.operator.name
            op_counts[op_name] = op_counts.get(op_name, 0) + 1
        print("Start times by operator:", op_counts)
finally:
    db.close()
