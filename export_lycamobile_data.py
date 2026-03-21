import pandas as pd
import sqlite3
import os

def export_lycamobile_data():
    # Connect to the database
    db_path = 'telecom_outage.db'
    if not os.path.exists(db_path):
        # Try finding it in backend/ if not in root
        db_path = os.path.join('backend', 'telecom_outage.db')
        if not os.path.exists(db_path):
            print(f"Error: telecom_outage.db not found.")
            return

    conn = sqlite3.connect(db_path)
    
    # Query Lycamobile outages (operator_id=3)
    query = """
    SELECT * FROM outages 
    WHERE operator_id = 3
    AND start_time IS NOT NULL AND start_time != ''
    AND estimated_fix_time IS NOT NULL AND estimated_fix_time != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No Lycamobile data found.")
        return

    # Filter: must have start_time AND estimated_fix_time
    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['estimated_fix_time'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce')

    # Excel does not support timezones
    if df['start_time'].dtype != 'datetime64[ns]':
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True).dt.tz_localize(None)
    if df['estimated_fix_time'].dtype != 'datetime64[ns]':
        df['estimated_fix_time'] = pd.to_datetime(df['estimated_fix_time'], utc=True).dt.tz_localize(None)
    
    df = df[df['start_time'].notna() & df['estimated_fix_time'].notna()]

    # Deduplication
    dedup_cols = ['title', 'description', 'location', 'start_time', 'estimated_fix_time']
    df = df.drop_duplicates(subset=dedup_cols)

    # Sort by location
    df = df.sort_values(by='location')

    # Export to Excel
    output_file = 'lycamobile_filtered_data.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Exported {len(df)} unique records to {output_file}")

if __name__ == "__main__":
    export_lycamobile_data()
