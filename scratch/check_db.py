import sqlite3

conn = sqlite3.connect('telecom_outage.db')
c = conn.cursor()

# List tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

# For each table, show columns and latest dates per operator
for (tname,) in tables:
    print(f"\n=== {tname} ===")
    c.execute(f"PRAGMA table_info({tname})")
    cols = c.fetchall()
    print("Columns:", [col[1] for col in cols])
    
    col_names = [col[1] for col in cols]
    
    # Try common date columns
    date_col = None
    for cand in ['start_time', 'created_at', 'timestamp', 'scraped_at', 'detected_at']:
        if cand in col_names:
            date_col = cand
            break
    
    operator_col = 'operator' if 'operator' in col_names else None
    
    if operator_col and date_col:
        c.execute(f"SELECT {operator_col}, MIN({date_col}), MAX({date_col}), COUNT(*) FROM {tname} GROUP BY {operator_col}")
        for row in c.fetchall():
            print(f"  {row[0]}: count={row[3]}, min={row[1]}, max={row[2]}")
    elif date_col:
        c.execute(f"SELECT MIN({date_col}), MAX({date_col}), COUNT(*) FROM {tname}")
        print(c.fetchone())

conn.close()