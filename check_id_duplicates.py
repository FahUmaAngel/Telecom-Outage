import sqlite3

def check_duplicates():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Find incident IDs that appear more than once
    cursor.execute("""
        SELECT incident_id, COUNT(*) 
        FROM outages 
        WHERE incident_id IS NOT NULL AND incident_id != ''
        GROUP BY incident_id 
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} duplicate incident IDs")
    
    for inc_id, _ in duplicates:
        cursor.execute("""
            SELECT id, operator_id, location, start_time, status 
            FROM outages 
            WHERE incident_id = ?
            ORDER BY id ASC
        """, (inc_id,))
        rows = cursor.fetchall()
        print(f"Incident {inc_id}:")
        for r in rows:
            print(f"  ID:{r[0]} Loc:{r[2]} Time:{r[3]} Status:{r[4]}")
        print("-" * 20)
    
    conn.close()

if __name__ == '__main__':
    check_duplicates()
