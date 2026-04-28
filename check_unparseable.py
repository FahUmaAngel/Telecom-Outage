import sqlite3
import pandas as pd

def check_unparseable(conn, op_name, op_id):
    print(f"\n--- {op_name} (ID: {op_id}) ---")
    df = pd.read_sql_query(f'SELECT id, start_time FROM outages WHERE operator_id={op_id}', conn)
    df['st_dt'] = pd.to_datetime(df['start_time'], errors='coerce')
    
    unparseable = df[df['st_dt'].isna()]
    print(f"Total unparseable start_time: {len(unparseable)}")
    
    if not unparseable.empty:
        print("Unique unparseable strings (first 50):")
        unique_vals = unparseable['start_time'].unique()
        for val in unique_vals[:50]:
            print(f'"{val}"')

def main():
    conn = sqlite3.connect('telecom_outage.db')
    check_unparseable(conn, 'telia', 1)
    check_unparseable(conn, 'lycamobile', 2)
    conn.close()

if __name__ == "__main__":
    main()
