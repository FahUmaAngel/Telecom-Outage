import sqlite3
import pandas as pd

def investigate():
    conn = sqlite3.connect('telecom_outage.db')
    
    print("--- Samples of records with 'län' but having Coords ---")
    query = """
    SELECT id, operator_id, location, latitude, longitude, start_time, estimated_fix_time 
    FROM outages 
    WHERE (location LIKE '% län%' OR location IS NULL OR location = 'Unknown')
    AND latitude IS NOT NULL AND longitude IS NOT NULL
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    print(df)
    
    print("\n--- Check for unusual empty dates ---")
    query = "SELECT start_time, COUNT(*) FROM outages GROUP BY start_time LIMIT 5"
    print(pd.read_sql_query(query, conn))
    
    conn.close()

if __name__ == "__main__":
    investigate()
