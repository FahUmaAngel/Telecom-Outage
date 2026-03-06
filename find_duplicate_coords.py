import sqlite3

def find_duplicate_coordinates():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Find coordinates that appear more than once
    query = """
        SELECT latitude, longitude, COUNT(*) as count
        FROM outages
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY latitude, longitude
        HAVING count > 1
    """
    cursor.execute(query)
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("No duplicate coordinates found.")
        conn.close()
        return

    print(f"Found {len(duplicates)} sets of duplicate coordinates:")
    print("-" * 50)
    
    for lat, lon, count in duplicates:
        print(f"Coordinates: ({lat}, {lon}) - Shared by {count} incidents")
        
        # List the incident IDs for these coordinates
        cursor.execute("""
            SELECT incident_id, title, operator_id
            FROM outages
            WHERE latitude = ? AND longitude = ?
        """, (lat, lon))
        incidents = cursor.fetchall()
        
        for inc_id, title, op_id in incidents:
            display_id = inc_id if inc_id else "No ID"
            print(f"  - {display_id}: {title} (Operator ID: {op_id})")
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    find_duplicate_coordinates()
