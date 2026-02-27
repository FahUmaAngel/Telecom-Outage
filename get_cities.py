import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Get cities for Tre
cursor.execute("""
    SELECT DISTINCT location 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name = 'tre' AND location IS NOT NULL;
""")
cities = [row[0] for row in cursor.fetchall()]

print(json.dumps(cities))
conn.close()
