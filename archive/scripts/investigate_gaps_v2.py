import sqlite3
import pandas as pd

def investigate():
    conn = sqlite3.connect('telecom_outage.db')
    
    # Check "län" records with coords
    query = """
    SELECT id, operator_id, location, latitude, longitude, start_time, estimated_fix_time 
    FROM outages 
    WHERE (location LIKE '% län%' OR location IS NULL OR location = 'Unknown' OR location = '')
    AND latitude IS NOT NULL AND longitude IS NOT NULL
    LIMIT 20
    """
    df_gaps = pd.read_sql_query(query, conn)
    df_gaps.to_csv('investigation_gaps.csv', index=False)
    
    # Check date issues
    query = """
    SELECT start_time, estimated_fix_time, COUNT(*) as count 
    FROM outages 
    WHERE operator_id IN (1, 3)
    GROUP BY start_time, estimated_fix_time
    LIMIT 20
    """
    df_dates = pd.read_sql_query(query, conn)
    df_dates.to_csv('investigation_dates.csv', index=False)
    
    conn.close()

if __name__ == "__main__":
    investigate()
