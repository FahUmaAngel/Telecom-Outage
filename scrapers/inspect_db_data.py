from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator
from sqlalchemy import func

def inspect_db():
    db = SessionLocal()
    try:
        # Check specifically for Tre outages
        tre_outages = db.query(Outage).join(Operator).filter(Operator.name == 'tre').all()
        print(f"\n--- Tre Outages Found: {len(tre_outages)} ---")
        for o in tre_outages:
            title_sv = o.title.get('sv', 'No SV Title') if isinstance(o.title, dict) else str(o.title)
            print(f"- Title: {title_sv}")
            print(f"  Updated: {o.updated_at}")
            print(f"  Desc: {str(o.description)[:50]}...")
            print("")
            
        print("\n---------------------------------")
        
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
