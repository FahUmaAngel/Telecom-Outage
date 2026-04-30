
from scrapers.db.connection import SessionLocal
from scrapers.db.models import Operator, Outage

db = SessionLocal()
ops = db.query(Operator).all()
outages = db.query(Outage).all()
print(f"Operators: {len(ops)}")
for op in ops:
    print(f" - {op.name}")
print(f"Outages: {len(outages)}")
db.close()
