
import sqlite3
import json

def audit():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get operators for mapping
    cursor.execute('SELECT id, name FROM operators')
    operators = {r[0]: r[1] for r in cursor.fetchall()}
    
    # Get offenses with Unknown location
    cursor.execute('SELECT operator_id, title, description, location FROM outages WHERE location = "Unknown"')
    rows = cursor.fetchall()
    
    print(f"Total 'Unknown' locations: {len(rows)}")
    for r in rows:
        op_name = operators.get(r[0], "unknown")
        title = r[1]
        desc = r[2]
        print(f"[{op_name}] Title: {title} | Desc: {desc[:100]}...")
        print("-" * 20)
    
    conn.close()

if __name__ == "__main__":
    audit()
