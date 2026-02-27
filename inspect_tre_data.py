import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Get column names
cursor.execute("PRAGMA table_info(outages);")
cols = [c[1] for c in cursor.fetchall()]
print(f"Columns: {cols}")

# Get first 10 Tre rows
cursor.execute("""
    SELECT * 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre'
    LIMIT 10;
""")
rows = cursor.fetchall()
for r in rows:
    # Print as dict for clarity
    print(dict(zip(cols, r)))

conn.close()
