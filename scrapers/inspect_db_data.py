from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Region
import json

def inspect_db():
    db = SessionLocal()
    try:
        outages = db.query(Outage).all()
        print(f"Total Outages: {len(outages)}")
        if outages:
            o = outages[0]
            print(f"Outage ID: {o.id}")
            print(f"Title type: {type(o.title)}")
            print(f"Title content: {o.title}")
            
            if o.region:
                print(f"Region Name type: {type(o.region.name)}")
                print(f"Region Name content: {o.region.name}")
            else:
                print("No region linked.")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
