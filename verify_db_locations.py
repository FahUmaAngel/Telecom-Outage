import sqlite3
import json

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    print("Checking active Telia outages...")
    cur.execute("""
        SELECT incident_id, location, region_id 
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'telia')
        AND location != 'Unknown'
        LIMIT 10
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Loc: {row[1]}, RID: {row[2]}")
        
    print("\nChecking Tre outages...")
    cur.execute("""
        SELECT incident_id, location, region_id 
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre')
        LIMIT 5
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Loc: {row[1]}, RID: {row[2]}")

    conn.close()

if __name__ == "__main__":
    main()
