import sqlite3
import json

def check_tre():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("SELECT id, name FROM operators WHERE name = 'tre'")
    op = cur.fetchone()
    if not op:
        print("Tre operator not found")
        return
    tre_id = op[0]
    
    print(f"Checking outages for Tre (ID: {tre_id})...")
    
    cur.execute("SELECT count(*) FROM outages WHERE operator_id = ?", (tre_id,))
    total = cur.fetchone()[0]
    print(f"Total Tre outages: {total}")
    
    cur.execute("SELECT count(*) FROM outages WHERE operator_id = ? AND incident_id IS NULL", (tre_id,))
    null_ids = cur.fetchone()[0]
    print(f"Tre outages with NULL incident_id: {null_ids}")
    
    cur.execute("SELECT incident_id, title FROM outages WHERE operator_id = ? AND incident_id IS NOT NULL LIMIT 10", (tre_id,))
    rows = cur.fetchall()
    print("\nSample Tre standardized data:")
    for r in rows:
        print(f"ID: {r[0]}, Title: {r[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_tre()
