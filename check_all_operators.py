import sqlite3
conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check all operator stats
cursor.execute("""
    SELECT operators.name, status, COUNT(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    GROUP BY operators.name, status;
""")
print("Outages by operator and status:")
for row in cursor.fetchall():
    print(row)

# Check for any operator with non-null start and end times where they are DIFFERENT
cursor.execute("""
    SELECT operators.name, COUNT(*) 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND start_time != end_time
    GROUP BY operators.name;
""")
print("\nOperators with valid MTTR-candidate outages (different start/end):")
print(cursor.fetchall())

conn.close()
