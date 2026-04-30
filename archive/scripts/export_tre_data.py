import pandas as pd
import sqlite3
import os

def export_tre_data():
    # Connect to the database
    db_path = 'telecom_outage.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    
    # Query Tre outages (operator_id=2)
    # We fetch all columns but specifically focus on the ones for deduplication if needed
    query = """
    SELECT * FROM outages 
    WHERE operator_id = 2
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No Tre data found.")
        return

    # Filter: must have start_time AND estimated_fix_time
    # First convert to datetime to be sure
    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['estimated_fix_time'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce')
    df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
    
    # User specifically asked for "start time and estimated fix time"
    df = df[df['start_time'].notna() & df['estimated_fix_time'].notna()]

    # Deduplication (Tre has duplicates from repetitive scraping)
    # We use a subset of columns that define a unique event
    dedup_cols = ['title', 'description', 'location', 'start_time', 'estimated_fix_time']
    # Drop rows where all these are duplicated
    df = df.drop_duplicates(subset=dedup_cols)

    # Sort by location (city)
    df = df.sort_values(by='location')

    # Export to Excel
    output_file = 'tre_filtered_data.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Exported {len(df)} unique records to {output_file}")

if __name__ == "__main__":
    export_tre_data()
