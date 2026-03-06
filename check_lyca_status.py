import sqlite3

conn = sqlite3.connect('telecom_outage.db')
res = conn.execute("""
    SELECT count(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'lycamobile'
""").fetchone()

print(f"Lyca count: {res[0]}")

res_end = conn.execute("""
    SELECT count(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'lycamobile' AND (end_time IS NOT NULL OR estimated_fix_time IS NOT NULL)
""").fetchone()

res_est = conn.execute("""
    SELECT count(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'lycamobile' AND estimated_fix_time IS NOT NULL
""").fetchone()

print(f"Lyca with estimated fix time: {res_est[0]}")
conn.close()
