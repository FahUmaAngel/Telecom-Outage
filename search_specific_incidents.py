import sqlite3
import json

def search():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    ids = ['INCSE0475544', 'INCSE0476740']
    
    print(f"Searching for {ids}...")
    # Use LIKE to be safe
    cursor.execute("SELECT incident_id, location, description FROM outages WHERE incident_id LIKE 'INCSE0475544%' OR incident_id LIKE 'INCSE0476740%'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No exact matches found. Searching for similar IDs...")
        cursor.execute("SELECT incident_id, location FROM outages WHERE incident_id LIKE 'INCSE047%' LIMIT 20")
        rows = cursor.fetchall()
        
    for row in rows:
        print(f"ID: {row[0]} | Location: {row[1]}")
        if len(row) > 2:
             print(f"Description: {row[2][:200]}...")
    
    conn.close()

if __name__ == "__main__":
    search()
