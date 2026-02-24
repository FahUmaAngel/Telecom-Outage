
import sqlite3
import json

def dump():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lycamobile sample
    cursor.execute('SELECT op.name, r.data FROM outages o JOIN operators op ON o.operator_id = op.id JOIN raw_data r ON o.raw_data_id = r.id WHERE o.location = "Unknown" AND op.name = "lycamobile" LIMIT 1')
    r = cursor.fetchone()
    if r:
        print(f"--- LYCAMOBILE ---")
        print(json.dumps(json.loads(r[1]), indent=2))
        
    # Telia sample
    cursor.execute('SELECT op.name, r.data FROM outages o JOIN operators op ON o.operator_id = op.id JOIN raw_data r ON o.raw_data_id = r.id WHERE o.location = "Unknown" AND op.name = "telia" LIMIT 1')
    r = cursor.fetchone()
    if r:
        print(f"--- TELIA ---")
        print(json.dumps(json.loads(r[1]), indent=2))
        
    conn.close()

if __name__ == "__main__":
    dump()
