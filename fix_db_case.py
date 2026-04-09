"""One-time script to normalize status/severity to lowercase."""
import sqlite3

conn = sqlite3.connect('telecom_outage.db', timeout=60)
cursor = conn.cursor()

cursor.execute("UPDATE outages SET status = LOWER(status) WHERE status <> LOWER(status)")
print(f"Status rows fixed: {cursor.rowcount}")

cursor.execute("UPDATE outages SET severity = LOWER(severity) WHERE severity <> LOWER(severity)")
print(f"Severity rows fixed: {cursor.rowcount}")

conn.commit()

cursor.execute("SELECT DISTINCT status FROM outages")
print("Distinct statuses:", [r[0] for r in cursor.fetchall()])

cursor.execute("SELECT DISTINCT severity FROM outages")
print("Distinct severities:", [r[0] for r in cursor.fetchall()])

conn.close()
print("Done!")
