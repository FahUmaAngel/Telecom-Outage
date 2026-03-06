import sqlite3
import json

def check_sources():
    try:
        conn = sqlite3.connect('telecom_outage.db')
        cur = conn.cursor()
        
        # Get Lycamobile ID
        cur.execute("SELECT id FROM operators WHERE name = 'lycamobile'")
        row = cur.fetchone()
        if not row: return
        lyca_id = row[0]
        
        # Check source for incidents without end times
        query = """
            SELECT raw_data.data, count(*)
            FROM outages 
            JOIN raw_data ON outages.raw_data_id = raw_data.id 
            WHERE outages.operator_id = ? 
            AND outages.end_time IS NULL 
            AND outages.estimated_fix_time IS NULL
            GROUP BY json_extract(raw_data.data, '$.source')
        """
        cur.execute(query, (lyca_id,))
        rows = cur.fetchall()
        
        print("Source distribution for Lycamobile with NO end dates:")
        for row in rows:
            data_sample = json.loads(row[0])
            source = data_sample.get('source', 'Unknown (Old format?)')
            count = row[1]
            print(f"Source: {source} | Count: {count}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sources()
