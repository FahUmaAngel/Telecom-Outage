import sys
import os
import json
from sqlalchemy.orm import Session
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator

def cleanup():
    db = SessionLocal()
    try:
        # Find operator IDs for Tre and Lycamobile
        operators = db.query(Operator).filter(Operator.name.in_(['tre', 'lycamobile'])).all()
        op_ids = [op.id for op in operators]
        
        if not op_ids:
            print("No operators found for cleanup.")
            return

        print(f"Starting cleanup for operators: {[op.name for op in operators]} (IDs: {op_ids})")
        
        # Fetch all outages for these operators
        outages = db.query(Outage).filter(Outage.operator_id.in_(op_ids)).all()
        
        updated_count = 0
        for outage in outages:
            if not outage.affected_services:
                continue
                
            # Current services (stored as JSON array in SQLite)
            services = outage.affected_services
            if not isinstance(services, list):
                continue
                
            # Filter out 'voice' and 'data'
            new_services = [s for s in services if s not in ['voice', 'data']]
            
            if len(new_services) != len(services):
                outage.affected_services = new_services
                outage.updated_at = datetime.utcnow()
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} outages (removed 'voice'/'data').")
        else:
            print("No outages required updates.")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
