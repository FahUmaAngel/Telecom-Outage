import sqlite3

db_path = 'telecom_outage.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT start_time, end_time, updated_at, status FROM outages WHERE operator_id = 2 AND status = 'resolved' LIMIT 1;")
row = cursor.fetchone()

print("Individual Record Inspection (Tre):")
if row:
    names = ["start_time", "end_time", "updated_at", "status"]
    for name, value in zip(names, row):
        print(f"{name}: {value} (Type: {type(value)})")
else:
    print("No resolved outages found for operator 2.")

conn.close()
