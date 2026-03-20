import sqlite3

def list_telia_missing():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage_copy.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        o.incident_id, 
        o.location, 
        o.title, 
        o.start_time
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'telia' 
    AND (o.latitude IS NULL OR o.longitude IS NULL)
    ORDER BY o.start_time DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Total Telia incidents missing coordinates: {len(rows)}")
    print("-" * 100)
    print(f"{'Incident ID':<20} | {'Location/Title':<50} | {'Start Time':<20}")
    print("-" * 100)
    
    for rid, loc, title, started in rows:
        display_name = loc if loc and loc != 'Unknown' else title
        print(f"{str(rid):<20} | {str(display_name):<50} | {str(started):<20}")
        
    conn.close()

if __name__ == "__main__":
    list_telia_missing()
