
import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RepairServices")

def repair():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    from scrapers.common.engine import classify_services
    
    logger.info(f"Connected to {db_path}")
    
    # Fetch all outages to re-classify them based on their descriptions
    cursor.execute('SELECT id, title, description, affected_services FROM outages')
    rows = cursor.fetchall()
    
    logger.info(f"Processing {len(rows)} outages for re-classification...")
    
    update_count = 0
    removed_5g_plus_count = 0
    
    for row in rows:
        outage_id, title_json, desc_json, old_services_json = row
        
        # Parse JSON fields (they are stored as strings in SQLite)
        try:
            title_sv = json.loads(title_json).get('sv', '') if title_json else ''
            desc_sv = json.loads(desc_json).get('sv', '') if desc_json else ''
            old_services = json.loads(old_services_json)
        except:
            continue
            
        context_text = f"{title_sv} {desc_sv}"
        new_services = [s.value for s in classify_services(context_text)]
        
        # Check if we removed 5G+
        if "5g+" in old_services and "5g+" not in new_services:
            removed_5g_plus_count += 1
            
        if set(old_services) != set(new_services):
            cursor.execute(
                'UPDATE outages SET affected_services = ? WHERE id = ?',
                (json.dumps(new_services), outage_id)
            )
            update_count += 1
            
    conn.commit()
    logger.info(f"✓ Re-classification complete.")
    logger.info(f"  - Total outages updated: {update_count}")
    logger.info(f"  - 5G+ removed from {removed_5g_plus_count} records where not explicitly mentioned.")
    
    conn.close()

if __name__ == "__main__":
    repair()
