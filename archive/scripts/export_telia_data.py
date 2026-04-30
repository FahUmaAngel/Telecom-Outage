import pandas as pd
import sqlite3
import os

def export_telia_data():
    # Connect to the database
    db_path = 'telecom_outage.db'
    if not os.path.exists(db_path):
        # Try finding it in backend/ if not in root
        db_path = os.path.join('backend', 'telecom_outage.db')
        if not os.path.exists(db_path):
            print("Error: telecom_outage.db not found.")
            return

    conn = sqlite3.connect(db_path)
    
    # Query Telia outages (operator_id=1)
    query = """
    SELECT * FROM outages 
    WHERE operator_id = 1 
    AND start_time IS NOT NULL AND start_time != ''
    AND estimated_fix_time IS NOT NULL AND estimated_fix_time != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Total Telia records from SQL: {len(df)}")
    if df.empty:
        return

    # Filter: must have start_time AND estimated_fix_time
    if not df['start_time'].empty:
        print("Example start_time raw:", df['start_time'].iloc[0])
    if not df['estimated_fix_time'].empty:
        print("Example estimated_fix_time raw:", df['estimated_fix_time'].iloc[0])

    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['estimated_fix_time'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce')
    
    # Excel does not support timezones, remove them
    if df['start_time'].dt.tz is not None:
        df['start_time'] = df['start_time'].dt.tz_localize(None)
    if df['estimated_fix_time'].dt.tz is not None:
        df['estimated_fix_time'] = df['estimated_fix_time'].dt.tz_localize(None)

    df_filtered = df[df['start_time'].notna() & df['estimated_fix_time'].notna()]
    print(f"Records after date filtering: {len(df_filtered)}")

    if df_filtered.empty:
        print("No records left after filtering.")
        return

    # Deduplication
    dedup_cols = ['title', 'description', 'location', 'start_time', 'estimated_fix_time']
    # Use a copy to avoid warnings
    df_dedup = df_filtered.copy()
    df_dedup = df_dedup.drop_duplicates(subset=dedup_cols)
    print(f"Records after deduplication: {len(df_dedup)}")

    # Sort by location
    df_dedup = df_dedup.sort_values(by='location')

    # Export to Excel
    output_file = 'telia_filtered_data.xlsx'
    df_dedup.to_excel(output_file, index=False)
    print(f"Exported {len(df_dedup)} unique records to {output_file}")

if __name__ == "__main__":
    export_telia_data()
