import sqlite3
import json

def fix():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Get all remaining bad location records for lycamobile
    cursor.execute("""
        SELECT id, incident_id, location, status
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name="lycamobile")
        AND location IN ('Sverige', 'Unknown')
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} records with Sverige/Unknown location")
    
    # For each, check if there's a newer record with the same incident_id but better location
    fixed = 0
    deleted_ids = []
    for outage_id, incident_id, location, status in rows:
        cursor.execute("""
            SELECT id, location FROM outages 
            WHERE incident_id = ? AND id != ? AND location NOT IN ('Sverige', 'Unknown')
        """, (incident_id, outage_id))
        duplicate = cursor.fetchone()
        
        if duplicate:
            print(f"  Deleting duplicate {outage_id} (incident {incident_id} loc={location}), better record at ID {duplicate[0]} (loc={duplicate[1]})")
            deleted_ids.append(outage_id)
        else:
            print(f"  Keeping {outage_id} (incident {incident_id}, no better record exists)")
    
    if deleted_ids:
        placeholders = ','.join(['?'] * len(deleted_ids))
        cursor.execute(f'DELETE FROM outages WHERE id IN ({placeholders})', deleted_ids)
        conn.commit()
        print(f"\n✓ Deleted {len(deleted_ids)} duplicate/outdated records with bad locations")
    
    conn.close()

if __name__ == '__main__':
    fix()
