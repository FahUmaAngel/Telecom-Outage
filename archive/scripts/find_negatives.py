import sqlite3
import pandas as pd

def find_negatives(conn, op_name, op_id):
    query = f"SELECT id, start_time, end_time, estimated_fix_time, location FROM outages WHERE operator_id = {op_id}"
    df = pd.read_sql_query(query, conn)
    
    df['st'] = pd.to_datetime(df['start_time'], errors='coerce', format='mixed', utc=True)
    df['et'] = pd.to_datetime(df['end_time'], errors='coerce', format='mixed', utc=True)
    df['eft'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce', format='mixed', utc=True)
    df['res'] = df['et'].fillna(df['eft'])
    
    neg = df[df['res'] < df['st']]
    print(f"\n--- Negative {op_name} (ID: {op_id}) ---")
    print(f"Total negative: {len(neg)}")
    for idx, row in neg.iterrows():
        print(f"ID {row['id']}: start={repr(row['start_time'])}, res={repr(row['end_time'] or row['estimated_fix_time'])}")

def main():
    conn = sqlite3.connect('telecom_outage.db')
    find_negatives(conn, 'telia', 1)
    find_negatives(conn, 'lycamobile', 2)
    conn.close()

if __name__ == "__main__":
    main()
