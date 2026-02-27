import sqlite3
import pandas as pd

def check_telia_locations():
    conn = sqlite3.connect('telecom_outage.db')
    query = """
    SELECT incident_id, location, latitude, longitude, operator 
    FROM outages 
    WHERE operator = 'telia'
    ORDER BY id DESC 
    LIMIT 30
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Last 30 Telia Outages:")
    print(df.to_string())
    
    unknown_count = len(df[df['location'].str.contains('Unknown', case=False)])
    print(f"\nPotential 'Unknown' in sample: {unknown_count}")

if __name__ == "__main__":
    check_telia_locations()
