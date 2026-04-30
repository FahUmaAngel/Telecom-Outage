import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def test_logic():
    conn = sqlite3.connect('telecom_outage.db')
    
    # Check a few records for Tre (ID 2) or Telia (ID 1)
    query = """
    SELECT id, start_time, end_time, estimated_fix_time 
    FROM outages 
    WHERE (end_time IS NOT NULL AND estimated_fix_time IS NOT NULL)
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    
    print("Found records with both end_time and estimated_fix_time:")
    for _, row in df.iterrows():
        st = pd.to_datetime(row['start_time'], utc=True)
        et = pd.to_datetime(row['end_time'], utc=True)
        eft = pd.to_datetime(row['estimated_fix_time'], utc=True)
        
        # New Logic: Priority end_time > estimated_fix_time
        res = et if pd.notna(et) else eft
        
        # Old potential logic check
        alt = eft if pd.notna(eft) else et
        
        diff_new = (res - st).total_seconds() / 3600
        diff_old = (alt - st).total_seconds() / 3600
        
        print(f"ID {row['id']}: ST={row['start_time']}, ET={row['end_time']}, EFT={row['estimated_fix_time']}")
        print(f"  MTTR (Priority ET): {diff_new:.2f}h")
        print(f"  MTTR (Old/Alt EFT): {diff_old:.2f}h")
        if et != eft:
            print("  --- DIFFERENT! ---")
    
    conn.close()

if __name__ == "__main__":
    test_logic()
