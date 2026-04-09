import sqlite3

def verify():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    ids = ['INCSE0424894', 'INCSE0342620', 'INCSE0425200', 'INCSE0424847']
    
    print("Final Verification for Specific Telia IDs:")
    print("-" * 60)
    
    cursor.execute("SELECT incident_id, latitude, longitude, location FROM outages WHERE incident_id IN (?,?,?,?)", ids)
    rows = cursor.fetchall()
    
    found_ids = [r[0] for r in rows]
    for r in rows:
        print(f"ID: {r[0]} | Lat: {r[1]} | Lon: {r[2]} | Loc: {r[3]}")
        
    for i in ids:
        if i not in found_ids:
            print(f"ID: {i} | NOT FOUND IN DATABASE")
            
    conn.close()

if __name__ == "__main__":
    verify()
