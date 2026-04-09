
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator
from sqlalchemy import func

def audit():
    db = SessionLocal()
    try:
        total = db.query(Outage).count()
        missing_coords = db.query(Outage).filter((Outage.latitude == None) | (Outage.longitude == None)).count()
        missing_end_date = db.query(Outage).filter(Outage.end_time == None).count()
        
        # Breakdown by operator
        operators = db.query(Operator).all()
        op_stats = []
        for op in operators:
            op_total = db.query(Outage).filter(Outage.operator_id == op.id).count()
            if op_total == 0: continue
            op_missing_coords = db.query(Outage).filter(Outage.operator_id == op.id).filter((Outage.latitude == None) | (Outage.longitude == None)).count()
            op_missing_end_date = db.query(Outage).filter(Outage.operator_id == op.id).filter(Outage.end_time == None).count()
            op_stats.append({
                "operator": op.name,
                "total": op_total,
                "missing_coords": op_missing_coords,
                "missing_end_date": op_missing_end_date,
                "quality_score": ((op_total - op_missing_coords - op_missing_end_date) / (op_total * 2 or 1)) * 100
            })

        print("=== DATA QUALITY AUDIT REPORT ===")
        print(f"Total Incidents: {total}")
        print(f"Missing Coordinates: {missing_coords} ({ (missing_coords/total*100) if total else 0 :.1f}%)")
        print(f"Missing End Dates: {missing_end_date} ({(missing_end_date/total*100) if total else 0 :.1f}%)")
        print("-" * 30)
        print(f"{'Operator':<15} | {'Total':<6} | {'No Coord':<9} | {'No End':<7} | {'Health'}")
        print("-" * 60)
        for stat in op_stats:
            health = f"{max(0, stat['quality_score']):.1f}%"
            print(f"{stat['operator']:<15} | {stat['total']:<6} | {stat['missing_coords']:<9} | {stat['missing_end_date']:<7} | {health}")
        print("=" * 30)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit()
