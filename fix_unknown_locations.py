import sys
import os
import sqlite3
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage, Operator
from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES
from scrapers.common.geocoding import get_county_coordinates
from datetime import datetime

def fix_locations():
    db = SessionLocal()
    try:
        # Fetch all outages with 'Unknown' location
        outages = db.query(Outage).filter(Outage.location == 'Unknown').all()
        
        print(f"Found {len(outages)} outages with 'Unknown' location.")
        
        fixed_count = 0
        for outage in outages:
            # Context for extraction: handle both dict and JSON string
            title_sv = ""
            desc_sv = ""
            
            try:
                title_data = outage.title
                if isinstance(title_data, str):
                    title_data = json.loads(title_data)
                title_sv = title_data.get('sv', '') if title_data else ''
                
                desc_data = outage.description
                if isinstance(desc_data, str):
                    desc_data = json.loads(desc_data)
                desc_sv = desc_data.get('sv', '') if desc_data else ''
            except Exception as e:
                print(f"Error parsing JSON for {outage.id}: {e}")
            
            context = f"{title_sv} {desc_sv}"
            if not context.strip():
                continue
            
            county_name = extract_region_from_text(context, SWEDISH_COUNTIES)
            if county_name:
                print(f"Fixed {outage.incident_id or outage.id}: Found '{county_name}' in context.")
                outage.location = county_name
                
                # Update coordinates
                coords = get_county_coordinates(county_name, jitter=True)
                if coords:
                    outage.latitude, outage.longitude = coords
                
                outage.updated_at = datetime.utcnow()
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"Successfully fixed {fixed_count} locations.")
        else:
            print("No locations could be fixed from existing text.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_locations()
