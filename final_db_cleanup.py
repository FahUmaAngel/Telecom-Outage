import sqlite3
import random
import logging
from scrapers.common.geocoding import SWEDISH_COUNTY_COORDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("FinalCleanup")

DB_PATH = "telecom_outage.db"

def apply_jitter(lat, lon, km=5.0):
    """Add a small random offset to coordinates (default 5km max)."""
    if lat is None or lon is None:
        return lat, lon
    # 1 km is roughly 0.009 degrees lat, 0.015 degrees lon in Sweden
    lat_jitter = (random.random() - 0.5) * 2 * (km * 0.009)
    lon_jitter = (random.random() - 0.5) * 2 * (km * 0.015)
    return lat + lat_jitter, lon + lon_jitter

def cleanup():
    logger.info("Starting final database cleanup and jittering...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Skip aggressive deduplication for now as Tre has None incident_ids
    logger.info("Skipping aggressive deduplication to prevent collapsing Tre records.")
    
    # 2. Identify records at exact county centers and apply jitter
    logger.info("Applying jitter to county-center coordinates...")
    jittered_count = 0
    
    # We look for lat/lon that match exactly the center points defined in SWEDISH_COUNTY_COORDS
    for county, (center_lat, center_lon) in SWEDISH_COUNTY_COORDS.items():
        # Find outages at this exact point
        cur.execute("""
            SELECT id, latitude, longitude FROM outages 
            WHERE abs(latitude - ?) < 0.000001 AND abs(longitude - ?) < 0.000001
        """, (center_lat, center_lon))
        
        rows = cur.fetchall()
        for row in rows:
            oid, lat, lon = row
            new_lat, new_lon = apply_jitter(lat, lon)
            cur.execute("UPDATE outages SET latitude = ?, longitude = ? WHERE id = ?", (new_lat, new_lon, oid))
            jittered_count += 1
            
    conn.commit()
    logger.info(f"Applied jitter to {jittered_count} records.")
    
    # 3. Final Summary Stats
    cur.execute("SELECT count(*) FROM outages")
    total = cur.fetchone()[0]
    logger.info(f"Final total outages: {total}")
    
    conn.close()

if __name__ == "__main__":
    cleanup()
