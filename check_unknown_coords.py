import sqlite3

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT incident_id, location, latitude, longitude
        FROM outages
        WHERE location = 'Unknown'
        AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
    """)
    rows = cur.fetchall()
    
    for r in rows[:10]:
        print(r)
        
    print(f"Total: {len(rows)}")

if __name__ == "__main__":
    main()
