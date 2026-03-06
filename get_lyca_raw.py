import sqlite3
import json

def get_lyca_sample():
    try:
        conn = sqlite3.connect('telecom_outage.db')
        cur = conn.cursor()
        query = """
            SELECT outages.id, outages.incident_id, raw_data.data 
            FROM outages 
            JOIN raw_data ON outages.raw_data_id = raw_data.id 
            JOIN operators ON outages.operator_id = operators.id 
            WHERE operators.name = 'lycamobile' 
            LIMIT 3
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        for row in rows:
            print(f"ID: {row[0]}, Incident ID: {row[1]}")
            data = json.loads(row[2])
            print(json.dumps(data, indent=2))
            print("-" * 30)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_lyca_sample()
