import sqlite3
import json

def list_bad_lyca():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    query = """
    SELECT o.id, o.incident_id, o.location, o.start_time, o.title, o.description
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'lycamobile' 
    AND o.location IN ('Sverige', 'Unknown', 'unknown', 'sverige')
    ORDER BY o.start_time DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} Lycamobile records with bad locations")
    
    for r in rows:
        print(f"DB_ID:{r[0]} INC_ID:{r[1]} Loc:{r[2]} Time:{r[3]}")
    
    conn.close()

if __name__ == '__main__':
    list_bad_lyca()
