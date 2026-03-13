import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("""
    SELECT o.incident_id, o.location, o.latitude, o.longitude, o.status
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'telia' AND o.incident_id IS NOT NULL
    ORDER BY o.updated_at DESC
    LIMIT 20
""")
rows = cur.fetchall()
print(f"Recent Telia incidents ({len(rows)} found):")
print(f"{'Incident ID':<20} {'Location':<35} {'Lat':<10} {'Lon':<10} {'Status'}")
print("-" * 90)
for r in rows:
    print(f"{r[0]:<20} {r[1]:<35} {str(r[2])[:8]:<10} {str(r[3])[:8]:<10} {r[4]}")
conn.close()
