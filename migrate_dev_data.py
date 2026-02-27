import sqlite3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("MigrateDevData")

LIVE_DB = "telecom_outage.db"
DEV_DB = "dev_import_source.db"

def migrate():
    logger.info("Starting migration from Dev branch database...")
    
    try:
        live_conn = sqlite3.connect(LIVE_DB)
        dev_conn = sqlite3.connect(DEV_DB)
        
        live_cur = live_conn.cursor()
        dev_cur = dev_conn.cursor()
        
        # 1. Map operators to ensure consistency
        dev_cur.execute("SELECT id, name FROM operators")
        dev_operators = {row[0]: row[1] for row in dev_cur.fetchall()}
        
        live_cur.execute("SELECT id, name FROM operators")
        live_operators = {row[1]: row[0] for row in live_cur.fetchall()}
        
        # Map for ID conversion
        op_id_map = {}
        for dev_id, name in dev_operators.items():
            if name not in live_operators:
                logger.info(f"Creating operator: {name}")
                live_cur.execute("INSERT INTO operators (name, created_at) VALUES (?, ?)", (name, datetime.now()))
                live_operators[name] = live_cur.lastrowid
            op_id_map[dev_id] = live_operators[name]
            
        # 2. Map regions
        dev_cur.execute("SELECT id, name FROM regions")
        dev_regions = {row[0]: row[1] for row in dev_cur.fetchall()}
        
        live_cur.execute("SELECT id, name FROM regions")
        live_regions = {row[1]: row[0] for row in live_cur.fetchall()}
        
        reg_id_map = {}
        for dev_id, name_json in dev_regions.items():
            if name_json not in live_regions:
                logger.debug(f"Creating region: {name_json}")
                live_cur.execute("INSERT INTO regions (name, created_at) VALUES (?, ?)", (name_json, datetime.now()))
                live_regions[name_json] = live_cur.lastrowid
            reg_id_map[dev_id] = live_regions[name_json]
            
        # 3. Fetch outages from Dev (specifically Dec 2025 as identified)
        # We also fetch raw_data to keep full fidelity
        query = """
            SELECT o.*, r.operator as raw_op, r.source_url, r.data as raw_json, r.scraped_at
            FROM outages o
            JOIN raw_data r ON o.raw_data_id = r.id
            WHERE o.start_time LIKE '2025-12%'
        """
        dev_cur.execute(query)
        dev_outages = dev_cur.fetchall()
        
        # Get column names for the outages table
        dev_cur.execute("PRAGMA table_info(outages)")
        columns = [col[1] for col in dev_cur.fetchall()]
        
        migrated_count = 0
        skipped_count = 0
        
        for row in dev_outages:
            # Create a dict for easier access (ignoring joined raw_data cols for now)
            item = dict(zip(columns, row))
            
            incident_id = item['incident_id']
            operator_id = op_id_map[item['operator_id']]
            
            # Check if exists in live
            live_cur.execute("SELECT id FROM outages WHERE incident_id = ? AND operator_id = ?", (incident_id, operator_id))
            if live_cur.fetchone():
                skipped_count += 1
                continue
                
            # Create RawData first
            raw_op = row[-4]
            raw_url = row[-3]
            raw_json = row[-2]
            raw_scraped = row[-1]
            
            live_cur.execute("""
                INSERT INTO raw_data (operator, source_url, data, scraped_at)
                VALUES (?, ?, ?, ?)
            """, (raw_op, raw_url, raw_json, raw_scraped))
            raw_id = live_cur.lastrowid
            
            # Insert Outage
            # Note: We need to handle IDs carefully
            live_cur.execute("""
                INSERT INTO outages (
                    incident_id, operator_id, region_id, raw_data_id,
                    title, description, status, severity,
                    start_time, end_time, estimated_fix_time,
                    location, latitude, longitude, affected_services,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['incident_id'],
                op_id_map[item['operator_id']],
                reg_id_map.get(item['region_id']),
                raw_id,
                item['title'],
                item['description'],
                item['status'],
                item['severity'],
                item['start_time'],
                item['end_time'],
                item['estimated_fix_time'],
                item['location'],
                item['latitude'],
                item['longitude'],
                item['affected_services'],
                item['created_at'],
                item['updated_at']
            ))
            
            migrated_count += 1
            
        live_conn.commit()
        logger.info(f"Migration complete: {migrated_count} records migrated, {skipped_count} skipped (duplicates).")
        
        live_conn.close()
        dev_conn.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()
