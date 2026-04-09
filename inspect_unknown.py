import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("""
    SELECT o.id, o.title, o.description 
    FROM outages o 
    JOIN operators op ON o.operator_id = op.id 
    WHERE o.location = 'Unknown' AND op.name = 'lycamobile' 
    LIMIT 20
""")
rows = cur.fetchall()

for row in rows:
    oid, title, desc = row
    print(f"ID: {oid}")
    print(f"Title: {title}")
    print(f"Desc: {desc}")
    print("-" * 20)

conn.close()
