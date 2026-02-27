import sqlite3
conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check Tre outages by status
cursor.execute("""
    SELECT status, COUNT(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre'
    GROUP BY status;
""")
print("Tre Statuses:")
print(cursor.fetchall())

# Check for Tre outages where start_time != end_time
cursor.execute("""
    SELECT incident_id, start_time, end_time, location, status
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND start_time != end_time
    LIMIT 10;
""")
diff_times = cursor.fetchall()
print("\nTre outages with DIFFERENT start and end times:")
for d in diff_times:
    print(d)

conn.close()
