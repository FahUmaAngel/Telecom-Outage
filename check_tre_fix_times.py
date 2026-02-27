import sqlite3
conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check Tre outages for estimated_fix_time
cursor.execute("""
    SELECT incident_id, start_time, end_time, estimated_fix_time, status
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND (end_time IS NOT NULL OR estimated_fix_time IS NOT NULL)
    LIMIT 20;
""")
rows = cursor.fetchall()
print("Tre outages with ANY fix time:")
for r in rows:
    print(r)

# Check count of Tre outages where estimated_fix_time is different from start_time
cursor.execute("""
    SELECT COUNT(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND start_time != estimated_fix_time AND estimated_fix_time IS NOT NULL;
""")
print(f"\nTre outages with different estimated_fix_time: {cursor.fetchone()[0]}")

conn.close()
