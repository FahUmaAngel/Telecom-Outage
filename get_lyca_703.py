import sqlite3
import json

def get_outage_raw(outage_id):
    try:
        conn = sqlite3.connect('telecom_outage.db')
        cur = conn.cursor()
        query = """
            SELECT outages.incident_id, raw_data.data 
            FROM outages 
            JOIN raw_data ON outages.raw_data_id = raw_data.id 
            WHERE outages.id = ?
        """
        cur.execute(query, (outage_id,))
        row = cur.fetchone()
        if row:
            print(f"Outage ID: {outage_id} | Incident ID: {row[0]}")
            print(json.dumps(json.loads(row[1]), indent=2))
        else:
            print(f"No record found for ID {outage_id}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_outage_raw(703)
