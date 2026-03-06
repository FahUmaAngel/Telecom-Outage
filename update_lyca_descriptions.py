import sqlite3
import json

def update_lyca_descriptions():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Get Lycamobile ID
    cur.execute("SELECT id FROM operators WHERE name = 'lycamobile'")
    row = cur.fetchone()
    if not row:
        print("Lycamobile operator not found.")
        return
    lyca_id = row[0]
    
    # Fetch all Lycamobile outages
    cur.execute("SELECT id, incident_id, description FROM outages WHERE operator_id = ?", (lyca_id,))
    outages = cur.fetchall()
    
    updated_count = 0
    for oid, iid, desc_json in outages:
        if not desc_json: continue
        
        try:
            desc = json.loads(desc_json)
        except:
            continue
            
        en_desc = desc.get('en', '')
        if en_desc == "Felsökning pågår":
            desc['en'] = "Troubleshooting in progress"
            new_desc_json = json.dumps(desc)
            cur.execute("UPDATE outages SET description = ? WHERE id = ?", (new_desc_json, oid))
            updated_count += 1
            
    conn.commit()
    print(f"Successfully updated {updated_count} Lycamobile descriptions.")
    conn.close()

if __name__ == "__main__":
    update_lyca_descriptions()
