import sqlite3

def find_missing_coordinates():
    # Use the copy to avoid locking issues
    conn = sqlite3.connect('d:/94 FAH works/Telecom-Outage/telecom_outage_copy.db')
    cursor = conn.cursor()
    
    # Query for incidents missing coordinates by operator
    query = """
        SELECT op.name, o.incident_id, o.location, o.title
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE (o.latitude IS NULL OR o.longitude IS NULL)
        AND op.name IN ('telia', 'lycamobile', 'tre')
        LIMIT 50
    """
    
    cursor.execute(query)
    missing = cursor.fetchall()
    
    if not missing:
        print("No incidents missing coordinates found for the specified operators.")
        conn.close()
        return

    print(f"Sample of incidents missing coordinates (List of first 50):")
    print("-" * 80)
    print(f"{'Operator':<12} | {'Incident ID':<20} | {'Location'}")
    print("-" * 80)
    
    for op_name, inc_id, loc, title in missing:
        display_id = inc_id if inc_id else "No ID"
        display_loc = loc if loc else title
        print(f"{op_name:<12} | {display_id:<20} | {display_loc}")
        
    # Get total counts per operator
    print("\nTotal Missing Counts per Operator:")
    print("-" * 30)
    cursor.execute("""
        SELECT op.name, COUNT(*) 
        FROM outages o 
        JOIN operators op ON o.operator_id = op.id 
        WHERE (o.latitude IS NULL OR o.longitude IS NULL) 
        GROUP BY op.name
    """)
    for name, count in cursor.fetchall():
        print(f"{name:<12}: {count}")

    conn.close()

if __name__ == "__main__":
    find_missing_coordinates()
