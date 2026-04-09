import sqlite3

def force_fix_all():
    db_paths = [
        'd:/94 FAH works/Telecom-Outage/telecom_outage.db',
        'd:/94 FAH works/Telecom-Outage/backend/telecom_outage.db'
    ]
    
    updates = [
        ('INCSE0424894', 57.7210, 12.9401, 'Borås'), 
        ('INCSE0342620', 62.3908, 17.3069, 'Sundsvall'), 
        ('INCSE0425200', 59.3293, 18.0686, 'Stockholm'), 
        ('INCSE0424847', 56.7165, 12.8202, 'Halland')
    ]
    
    for db_path in db_paths:
        print(f"Targeting: {db_path}...")
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            cursor = conn.cursor()
            
            for inc_id, lat, lon, loc in updates:
                cursor.execute("""
                    UPDATE outages 
                    SET latitude = ?, longitude = ?, location = ? 
                    WHERE incident_id = ? 
                    AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
                """, (lat, lon, loc, inc_id))
                print(f"  Attempted {inc_id} -> {loc}")
                
            conn.commit()
            print(f"  Committed changes to {db_path}")
            
            # Verify immediately
            cursor.execute("SELECT incident_id, latitude FROM outages WHERE incident_id IN ('INCSE0424894', 'INCSE0342620', 'INCSE0425200', 'INCSE0424847')")
            for r in cursor.fetchall():
                print(f"    Verification: {r[0]} -> {r[1]}")
                
            conn.close()
        except Exception as e:
            print(f"  Error accessing {db_path}: {e}")

if __name__ == "__main__":
    force_fix_all()
