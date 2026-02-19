import sqlite3
import json
import os
import sys

# Add scrapers directory to path to use engine/models
sys.path.append(os.path.join(os.getcwd(), 'scrapers'))

from common.models import OutageStatus, ServiceType
from common.engine import classify_services, classify_status

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def repair():
    print(f"Repairing data in {db_path}...")
    
    # Get all outages with their titles and descriptions
    cursor.execute("SELECT id, title, description, status, affected_services FROM outages")
    outages = cursor.fetchall()
    
    updated_count = 0
    
    for row in outages:
        oid, title_json, desc_json, current_status, current_services_json = row
        
        try:
            title_dict = json.loads(title_json) if title_json else {}
            desc_dict = json.loads(desc_json) if desc_json else {}
            
            # Use both SV and EN for classification
            context = f"{title_dict.get('sv', '')} {title_dict.get('en', '')} {desc_dict.get('sv', '')} {desc_dict.get('en', '')}"
            
            new_services = classify_services(context)
            
            # Map current status safely
            try:
                if current_status:
                    base_status = OutageStatus(current_status.lower())
                else:
                    base_status = OutageStatus.ACTIVE
            except ValueError:
                base_status = OutageStatus.ACTIVE
                
            new_status = classify_status(context, base_status)
            
            new_services_json = json.dumps([s.value for s in new_services])
            new_status_val = new_status.name # Store member name (UPPERCASE)
            
            # Check if any change is needed
            if new_services_json != current_services_json or new_status_val != current_status:
                cursor.execute("""
                    UPDATE outages 
                    SET affected_services = ?, status = ?
                    WHERE id = ?
                """, (new_services_json, new_status_val, oid))
                updated_count += 1
                
        except Exception as e:
            print(f"Error processing outage {oid}: {e}")
            
    conn.commit()
    print(f"Successfully updated {updated_count} out of {len(outages)} records.")
    
if __name__ == "__main__":
    repair()
    conn.close()
