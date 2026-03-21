import sqlite3

db_path = 'telecom_outage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get Tre ID
cursor.execute("SELECT id FROM operators WHERE name = 'tre' COLLATE NOCASE;")
tre_id = cursor.fetchone()[0]

print(f"Status dump for ALL records for Tre (ID: {tre_id})")

# Fetch status and incident_id for ALL records
cursor.execute(f"SELECT status, incident_id FROM outages WHERE operator_id = {tre_id};")
rows = cursor.fetchall()

status_map = {}
for status, inc_id in rows:
    s_repr = repr(status)
    status_map[s_repr] = status_map.get(s_repr, 0) + 1

print("\nStatus distribution (with repr):")
for s_repr, count in status_map.items():
    print(f" {s_repr}: {count}")

conn.close()
