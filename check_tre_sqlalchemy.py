from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator

db = SessionLocal()
tre_op = db.query(Operator).filter(Operator.name == 'tre').first()
if tre_op:
    outages = db.query(Outage).filter(Outage.operator_id == tre_op.id).all()
    print(f"SQLAlchemy found {len(outages)} Tre outages.")
    for o in outages[:5]:
        print(f"ID: {o.id}, Status: {o.status}, Operator: {o.operator.name}")
else:
    print("Tre operator not found.")
db.close()
