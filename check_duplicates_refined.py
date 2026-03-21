import sqlite3

def check_duplicates():
    # Use the copy to avoid locking issues
    conn = sqlite3.connect('d:/94 FAH works/Telecom-Outage/telecom_outage_copy.db')
    cursor = conn.cursor()
    
    query = """
    SELECT 
        o.latitude, 
        o.longitude, 
        COUNT(*) as total_count,
        GROUP_CONCAT(DISTINCT op.name) as operator_names
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE o.latitude IS NOT NULL 
    GROUP BY o.latitude, o.longitude
    HAVING total_count > 1
    ORDER BY total_count DESC
    """
    
    print("Checking for duplicate coordinates across all operators...")
    print("-" * 60)
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No duplicate coordinates found.")
        return

    cross_op_count = 0
    total_sets = len(rows)
    
    for lat, lon, count, ops in rows:
        is_cross = "," in ops
        if is_cross:
            cross_op_count += 1
            status = " [SHARED]"
        else:
            status = ""
            
        print(f"Loc: ({lat}, {lon}) | Count: {count} | Operators: {ops}{status}")
    
    print("-" * 60)
    print(f"Summary: Found {total_sets} locations with multiple incidents.")
    print(f"Shared locations (Cross-Operator): {cross_op_count}")
    
    conn.close()

if __name__ == "__main__":
    check_duplicates()
