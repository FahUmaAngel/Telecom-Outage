import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check Tre outages specifically
cursor.execute("""
    SELECT incident_id, start_time, end_time, location, status, updated_at, created_at
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre'
    LIMIT 20;
""")
outages = cursor.fetchall()
print("Sample Tre data (first 20):")
for o in outages:
    print(o)

# Check all Tre outages status
cursor.execute("""
    SELECT status, COUNT(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre'
    GROUP BY status;
""")
print("\nTre outages by status:")
print(cursor.fetchall())

# Check for non-null start_time and end_time specifically
cursor.execute("""
    SELECT COUNT(*) FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND start_time IS NOT NULL;
""")
print(f"\nTre outages with start_time: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND end_time IS NOT NULL;
""")
print(f"Tre outages with end_time: {cursor.fetchone()[0]}")

conn.close()
