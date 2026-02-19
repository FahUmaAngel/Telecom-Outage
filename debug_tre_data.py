import sqlite3
import json

def check():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Check Tre outages
    cursor.execute("SELECT id, title, description, affected_services FROM outages WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre') LIMIT 5")
    rows = cursor.fetchall()
    
    print("--- Tre Outages ---")
    for row in rows:
        oid, title, desc, services = row
        print(f"ID: {oid}")
        print(f"Title: {title}")
        print(f"Desc: {desc}")
        print(f"Services: {services}")
        print("-" * 20)
        
    conn.close()

if __name__ == "__main__":
    check()
