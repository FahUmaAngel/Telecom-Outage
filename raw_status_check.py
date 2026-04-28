import sqlite3

db_path = 'telecom_outage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get Tre ID
cursor.execute("SELECT id FROM operators WHERE name = 'tre' COLLATE NOCASE;")
tre_id = cursor.fetchone()[0]

print(f"Raw data inspection for Tre (ID: {tre_id})")

# Fetch one record to see status field
cursor.execute("SELECT status FROM outages WHERE operator_id = %s LIMIT 1;", tre_id)
raw_status = cursor.fetchone()[0]
print(f"Raw status: {repr(raw_status)}")

# Check if maybe it's lowercase 'resolved' but my previous check was case-sensitive?
# My previous fine-grained said 'Resolved' (count 537)
# But my = 'Resolved' failed. This is extremely weird.

# Let's check the hex representation of the status if it exists
cursor.execute("SELECT hex(status) FROM outages WHERE operator_id = %s LIMIT 1;", (tre_id,))
print(f"Hex status: {cursor.fetchone()[0]}")

conn.close()
