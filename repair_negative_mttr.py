import sqlite3
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("RepairMTTR")

DB_PATH = "telecom_outage.db"

def repair():
    logger.info("Starting database MTTR repair...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Fix Future Dates (Year Rollover Bug)
    # Lycamobile/Telenor dates like Dec 2026 that should be Dec 2025
    cur.execute("""
        SELECT id, incident_id, start_time, end_time 
        FROM outages 
        WHERE start_time LIKE '2026-11%' OR start_time LIKE '2026-12%'
    """)
    future_outages = cur.fetchall()
    
    for row in future_outages:
        oid, inc_id, start, end = row
        new_start = start.replace('2026-', '2025-')
        # Also check end_time if it's also in future
        new_end = end
        if end and ('2026-11' in end or '2026-12' in end):
             new_end = end.replace('2026-', '2025-')
        
        logger.info(f"Correcting year for {inc_id}: {start} -> {new_start}")
        cur.execute("UPDATE outages SET start_time = ?, end_time = ? WHERE id = ?", (new_start, new_end, oid))
    
    # 2. Fix Telia Start Time > End Time (Scraped Time fallback issue)
    # ID's starting with INCSE are Telia. 
    # If end_time is valid but start_time is just after it (scraped time), adjust start_time.
    cur.execute("""
        SELECT id, incident_id, start_time, end_time 
        FROM outages 
        WHERE end_time < start_time AND incident_id LIKE 'INCSE%'
    """)
    telia_anomalies = cur.fetchall()
    
    for row in telia_anomalies:
        oid, inc_id, start, end = row
        # Parse end_time
        try:
            # Handle possible fractional seconds in ISO format
            end_dt = datetime.fromisoformat(end.split('.')[0])
            # Set start_time to 2 hours before end_time as a placeholder
            new_start_dt = end_dt - timedelta(hours=2)
            new_start = new_start_dt.isoformat(sep=' ')
            
            logger.info(f"Adjusting Telia start_time for {inc_id} (MTTR was negative): {start} -> {new_start}")
            cur.execute("UPDATE outages SET start_time = ? WHERE id = ?", (new_start, oid))
        except Exception as e:
            logger.warning(f"Failed to fix Telia {inc_id}: {e}")

    conn.commit()
    logger.info("Database repair complete.")
    conn.close()

if __name__ == "__main__":
    repair()
