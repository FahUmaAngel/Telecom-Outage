import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check Tre outages specifically
cursor.execute("""
    SELECT incident_id, start_time, end_time, location, status
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre'
    LIMIT 20;
""")
outages = cursor.fetchall()
for o in outages:
    print(o)

# Check count of Tre outages with non-null start and end times
cursor.execute("""
    SELECT COUNT(*) FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND start_time IS NOT NULL AND end_time IS NOT NULL;
""")
print(f"Total resolved Tre outages: {cursor.fetchone()[0]}")

# Check count of Tre outages with non-null start time but null end time
cursor.execute("""
    SELECT COUNT(*) FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND start_time IS NOT NULL AND end_time IS NULL;
""")
print(f"Total active/incomplete Tre outages: {cursor.fetchone()[0]}")

conn.close()
