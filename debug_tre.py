import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()

# Check operator names
cursor.execute("SELECT name FROM operators;")
operators = [row[0] for row in cursor.fetchall()]
print(f"Operators: {operators}")

# Check sample Tre outages
cursor.execute("""
    SELECT incident_id, title, location, region_id 
    FROM outages 
    JOIN operators ON outages.operator_id = operators.id 
    WHERE operators.name LIKE '%Tre%' LIMIT 5;
""")
samples = cursor.fetchall()
print(f"Sample Tre Outages: {samples}")

conn.close()
