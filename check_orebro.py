import sqlite3

def check_orebro():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    # Find all telia outages where description contains Örebro
    cursor.execute("""
        SELECT i.incident_id, i.location, i.description 
        FROM outages i
        JOIN operators o ON i.operator_id = o.id
        WHERE o.name = 'telia' AND (i.description LIKE '%Örebro%' OR i.description LIKE '%Orebro%')
    """)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} incidents mentioning Örebro:")
    for r in rows:
        print(f"ID: {r[0]} | Current Location: {r[1]}")
        desc = r[2]
        print(f"Desc snippet: {desc[:200]}")
        print("---")
        
    # Also just list the last 15 telia records to see if location extraction was fully broken
    print("\nLast 15 Telia Records:")
    cursor.execute("""
        SELECT i.incident_id, i.location
        FROM outages i
        JOIN operators o ON i.operator_id = o.id
        WHERE o.name = 'telia'
        ORDER BY i.id DESC LIMIT 15
    """)
    for r in cursor.fetchall():
        print(f"{r[0]}: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_orebro()
