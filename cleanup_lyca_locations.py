import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CleanupLyca")

def cleanup():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Identify incident_ids that have both a 'bad' location and a 'good' location
    # Bad locations: 'Unknown', 'Sverige', 'unknown', 'sverige'
    
    query = """
    SELECT incident_id 
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'lycamobile'
    AND incident_id IS NOT NULL AND incident_id != ''
    GROUP BY incident_id
    HAVING COUNT(*) > 1
    """
    
    cursor.execute(query)
    incident_ids = [row[0] for row in cursor.fetchall()]
    print(f"Checking {len(incident_ids)} potential duplicate Lycamobile IDs...")
    
    resolved_count = 0
    for inc_id in incident_ids:
        # Get all records for this ID
        cursor.execute("""
            SELECT id, location, start_time 
            FROM outages 
            WHERE incident_id = ?
            ORDER BY CASE WHEN location IN ('Unknown', 'Sverige', 'unknown', 'sverige') THEN 1 ELSE 0 END ASC, 
                     start_time DESC
        """, (inc_id,))
        rows = cursor.fetchall()
        
        # The first row (index 0) is the "best" record because it's sorted with 'good' locations first
        best_id, best_loc, best_time = rows[0]
        
        if best_loc not in ('Unknown', 'Sverige', 'unknown', 'sverige'):
            # Delete all OTHER records for this incident_id that are bad
            cursor.execute("""
                DELETE FROM outages 
                WHERE incident_id = ? 
                AND id != ? 
                AND location IN ('Unknown', 'Sverige', 'unknown', 'sverige')
            """, (inc_id, best_id))
            if cursor.rowcount > 0:
                print(f"Resolved Location for ID {inc_id} -> {best_loc} (Deleted {cursor.rowcount} bad records)")
                resolved_count += 1

    conn.commit()
    print(f"Finished. Resolved {resolved_count} locations and cleaned up duplicates.")
    conn.close()

if __name__ == '__main__':
    cleanup()
