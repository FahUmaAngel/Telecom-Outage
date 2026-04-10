import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from populate_historical import RECOVERED_INCIDENTS
from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage

def restore():
    db = SessionLocal()
    try:
        updated = 0
        for inc in RECOVERED_INCIDENTS:
            existing = db.query(Outage).filter(Outage.incident_id == inc["incident_id"]).first()
            if existing:
                # Get the explicitly assigned services from the historical data
                historical_services = inc.get("affected_services", [])
                
                # Make them lowercase to match the new standardization
                standardized = sorted([str(s).lower() for s in historical_services])
                
                # Update the database
                current = sorted(existing.affected_services or [])
                if current != standardized:
                    existing.affected_services = standardized
                    updated += 1
                    print(f"Restored {inc['incident_id']} from {current} -> {standardized}")
        
        db.commit()
        print(f"\nSuccessfully restored 2G/3G/4G/5G classifications for {updated} historical incidents.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore()
