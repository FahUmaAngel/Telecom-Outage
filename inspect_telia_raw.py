import sqlite3
import json

def inspect_raw():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Get one of the unknown telia incidents
    cur.execute('''
        SELECT o.incident_id, r.data 
        FROM outages o 
        JOIN raw_data r ON o.raw_data_id = r.id 
        WHERE o.incident_id = "INCSE0424841"
    ''')
    row = cur.fetchone()
    if row:
        print(f"Incident: {row[0]}")
        data = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        print(json.dumps(data, indent=2))
    else:
        print("Not found")
        
    conn.close()

if __name__ == '__main__':
    inspect_raw()
