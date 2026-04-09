import sqlite3
import json

def analyze_lyca_titles():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Get Lycamobile ID first
    cur.execute("SELECT id FROM operators WHERE name = 'lycamobile'")
    row = cur.fetchone()
    if not row:
        print("Lycamobile operator not found.")
        return
    lyca_id = row[0]
    
    # Fetch all Lycamobile outages
    cur.execute("SELECT id, incident_id, title FROM outages WHERE operator_id = ?", (lyca_id,))
    outages = cur.fetchall()
    
    mismatches = []
    for oid, iid, title_json in outages:
        if not iid: continue
        
        try:
            title = json.loads(title_json)
        except:
            print(f"Error parsing JSON for ID {oid}")
            continue
            
        sv = title.get('sv')
        en = title.get('en')
        
        if sv != iid or en != iid:
            mismatches.append({
                'id': oid,
                'incident_id': iid,
                'current_sv': sv,
                'current_en': en
            })
            
    print(f"Total Lycamobile outages checked: {len(outages)}")
    print(f"Total mismatches found: {len(mismatches)}")
    
    if mismatches:
        print("\nFirst 10 mismatches:")
        for m in mismatches[:10]:
            print(f"ID: {m['id']} | Incident ID: {m['incident_id']} | SV: {m['current_sv']} | EN: {m['current_en']}")

if __name__ == "__main__":
    analyze_lyca_titles()
