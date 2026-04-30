import sqlite3
import pandas as pd
import datetime

def audit(conn, op_name, op_id):
    print(f"\n=== AUDIT FOR {op_name} (ID: {op_id}) ===")
    
    # Load all records
    df = pd.read_sql_query(f"SELECT * FROM outages WHERE operator_id = {op_id}", conn)
    print(f"Total records in DB: {len(df)}")
    
    if df.empty:
        return

    # Check for NULLs/Empty in SQL
    empty_start = df[df['start_time'].isna() | (df['start_time'] == '')]
    print(f"Empty start_time in DB: {len(empty_start)}")

    # Check parsing with pd.to_datetime using format='mixed' and utc=True
    df['st_dt'] = pd.to_datetime(df['start_time'], errors='coerce', format='mixed', utc=True)
    df['et_dt'] = pd.to_datetime(df['end_time'], errors='coerce', format='mixed', utc=True)
    df['eft_dt'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce', format='mixed', utc=True)
    
    fail_count = df['st_dt'].isna().sum() - len(empty_start)
    print(f"Successfully parsed by pd.to_datetime: {df['st_dt'].notna().sum()}")
    print(f"Failed to parse (coerced to NaT): {fail_count}")
    
    if fail_count > 0:
        unparseable = df[df['st_dt'].isna() & ~df.index.isin(empty_start.index)]
        print("First 20 unparseable strings:")
        for idx, row in unparseable.head(20).iterrows():
            print(f"ID {row['id']}: {repr(row['start_time'])}")

    # Check the negative duration logic
    df_p = df[df['st_dt'].notna()].copy()
    df_p['res'] = df_p['et_dt'].fillna(df_p['eft_dt'])
    
    # Rows with both start and resolved_at
    df_timed = df_p[df_p['res'].notna()].copy()
    print(f"Records with both start and end/estimate: {len(df_timed)}")
    
    # Negative durations
    neg = df_timed[df_timed['res'] < df_timed['st_dt']]
    print(f"Negative durations: {len(neg)}")
    if not neg.empty:
        print("First 10 negative duration records:")
        for idx, row in neg.head(10).iterrows():
            diff = (row['res'] - row['st_dt']).total_seconds() / 3600
            print(f"ID {row['id']}: start={row['start_time']}, res={row['res']}, diff_hours={diff:.2f}, location={row['location']}")

    # Location check
    has_lan = df_timed[df_timed['location'].str.contains('län', case=False, na=False)]
    print(f"Records already containing 'län' (and having timestamps): {len(has_lan)}")
    
    generic = df_timed[~df_timed['location'].str.contains('län', case=False, na=False)]
    print(f"Generic or other locations remaining: {len(generic)}")
    if len(generic) > 0:
        print("First 10 non-län locations:")
        print(generic['location'].head(10).tolist())

def main():
    conn = sqlite3.connect('telecom_outage.db')
    audit(conn, "telia", 1)
    audit(conn, "lycamobile", 2)
    conn.close()

if __name__ == "__main__":
    main()
