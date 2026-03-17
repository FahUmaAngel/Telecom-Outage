import sqlite3

def check_data():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", cur.fetchall())
    
    # Check some outages and their regions
    cur.execute("""
        SELECT o.incident_id, o.location, r.name 
        FROM outages o 
        LEFT JOIN regions r ON o.region_id = r.id 
        LIMIT 10
    """)
    print("\nSample Data (Incident ID, Location, Region Name):")
    for row in cur.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_data()
