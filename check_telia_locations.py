import sqlite3

def check_db():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    # Check all telia outages
    cur.execute("""
        SELECT o.incident_id, o.location, r.name, o.region_id
        FROM outages o
        LEFT JOIN operators op ON o.operator_id = op.id
        LEFT JOIN regions r ON o.region_id = r.id
        WHERE op.name = 'telia'
    """)
    rows = cur.fetchall()
    
    print(f"Total Telia outages: {len(rows)}")
    missing_region = [r for r in rows if r[3] is None]
    print(f"Telia outages with missing region_id: {len(missing_region)}")
    
    print("\nSample missing region:")
    for r in missing_region[:10]:
        print(f"  ID: {r[0]}, Location: {r[1]}, Region ID: {r[3]}")
        
    print("\nSample with region:")
    with_region = [r for r in rows if r[3] is not None]
    for r in with_region[:10]:
        print(f"  ID: {r[0]}, Location: {r[1]}, Region Name: {r[2]}")
        
    conn.close()

if __name__ == '__main__':
    check_db()
