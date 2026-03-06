import sqlite3
import json

def update_lyca_titles():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Get Lycamobile ID
    cur.execute("SELECT id FROM operators WHERE name = 'lycamobile'")
    row = cur.fetchone()
    if not row:
        print("Lycamobile operator not found.")
        return
    lyca_id = row[0]
    
    # Fetch mismatched Lycamobile outages
    cur.execute("SELECT id, incident_id, title FROM outages WHERE operator_id = ?", (lyca_id,))
    outages = cur.fetchall()
    
    updated_count = 0
    for oid, iid, title_json in outages:
        if not iid: continue
        
        try:
            title = json.loads(title_json)
        except:
            continue
            
        sv = title.get('sv')
        en = title.get('en')
        
        if sv != iid or en != iid:
            new_title = json.dumps({"sv": iid, "en": iid})
            cur.execute("UPDATE outages SET title = ? WHERE id = ?", (new_title, oid))
            updated_count += 1
            
    conn.commit()
    print(f"Successfully updated {updated_count} Lycamobile titles.")
    conn.close()

if __name__ == "__main__":
    update_lyca_titles()
