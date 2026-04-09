import sqlite3

def filter_incidents_by_date():
    conn = sqlite3.connect('telecom_outage.db')
    c = conn.cursor()
    
    query = """
    SELECT incident_id, start_time 
    FROM outages 
    WHERE latitude = 58.0 AND longitude = 14.0
    """
    c.execute(query)
    rows = c.fetchall()
    
    start_filter = '2026-02-04'
    end_filter = '2026-03-06T23:59:59'
    
    results = []
    for inc_id, start_time in rows:
        if start_time and start_filter <= start_time <= end_filter:
            results.append(f"{inc_id} ({start_time})")
            
    if results:
        print("\n".join(results))
        print(f"\nTotal: {len(results)}")
    else:
        print("No incidents found in this date range.")
        
    conn.close()

if __name__ == "__main__":
    filter_incidents_by_date()
