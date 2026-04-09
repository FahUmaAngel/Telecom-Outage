import sqlite3

def find_null_end_times():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    # Query incidents that have an incident_id (INCSE...) but NO end_time
    cursor.execute("SELECT incident_id FROM outages WHERE end_time IS NULL AND incident_id IS NOT NULL")
    rows = cursor.fetchall()
    
    print("Incidents missing End Date:")
    for r in rows:
        print(r[0])
    
    conn.close()

if __name__ == "__main__":
    find_null_end_times()
