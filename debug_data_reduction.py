import sqlite3
import pandas as pd
import os

def debug_data_reduction(conn, op_name, op_id):
    print(f"\n--- Debugging {op_name} (ID: {op_id}) ---")
    
    query = f"SELECT * FROM outages WHERE operator_id = {op_id}"
    df = pd.read_sql_query(query, conn)
    total_initial = len(df)
    print(f"Total initial records: {total_initial}")

    # 1. Missing start_time
    missing_start = df[df['start_time'].isna() | (df['start_time'] == '')]
    print(f"Missing start_time: {len(missing_start)}")

    # 2. Missing both end_time and estimated_fix_time
    df_with_start = df[~df.index.isin(missing_start.index)]
    missing_both_end = df_with_start[
        (df_with_start['end_time'].isna() | (df_with_start['end_time'] == '')) & 
        (df_with_start['estimated_fix_time'].isna() | (df_with_start['estimated_fix_time'] == ''))
    ]
    print(f"Missing both end/estimate (with start_time): {len(missing_both_end)}")

    # 3. Location issues (Unknown/Sverige and not geocodable)
    # We'll just check how many are 'Unknown' or 'Sverige' or NULL
    location_issues = df_with_start[
        (df_with_start['location'].isna()) | 
        (df_with_start['location'].isin(['Unknown', 'Sverige', '']))
    ]
    print(f"Generic/Missing location: {len(location_issues)}")

    # 4. Negative Duration
    df_valid_times = df_with_start[~df_with_start.index.isin(missing_both_end.index)].copy()
    df_valid_times['start_time'] = pd.to_datetime(df_valid_times['start_time'], errors='coerce')
    df_valid_times['end_time'] = pd.to_datetime(df_valid_times['end_time'], errors='coerce')
    df_valid_times['estimated_fix_time'] = pd.to_datetime(df_valid_times['estimated_fix_time'], errors='coerce')
    
    df_valid_times['resolved_at'] = df_valid_times['end_time'].fillna(df_valid_times['estimated_fix_time'])
    
    negative_duration = df_valid_times[df_valid_times['resolved_at'] < df_valid_times['start_time']]
    print(f"Negative durations: {len(negative_duration)}")
    if not negative_duration.empty:
        print("Sample negative durations:")
        print(negative_duration[['incident_id', 'start_time', 'resolved_at', 'location']].head(5).to_string())

def main():
    conn = sqlite3.connect('telecom_outage.db')
    debug_data_reduction(conn, "telia", 1)
    debug_data_reduction(conn, "lycamobile", 2)
    conn.close()

if __name__ == "__main__":
    main()
