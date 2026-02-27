import sqlite3
import json

def check_unknowns():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.incident_id, i.description 
        FROM outages i 
        JOIN operators o ON i.operator_id = o.id 
        WHERE o.name = 'telia' AND i.location = 'Unknown'
    """)
    rows = cursor.fetchall()
    print(f"Total Unknown Telia: {len(rows)}")
    for r in rows[:10]:
        print(f"ID: {r[0]}")
        try:
            desc = json.loads(r[1])
            print(f"Desc: {desc.get('sv', '')}")
        except:
            print(f"Desc: {r[1]}")
        print("---")
    conn.close()

if __name__ == "__main__":
    check_unknowns()
