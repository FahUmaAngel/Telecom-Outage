import sqlite3
import json
import re

def check_swedish_descriptions():
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
    
    # Common Swedish words in outage descriptions
    sw_indicators = [
        r'\bpågår\b', r'\bfelsökning\b', r'\bunderhåll\b', r'\barbete\b', 
        r'\bproblem\b', r'\btäckning\b', r'\bområde\b', r'\bklart\b',
        r'\berfara\b', r'\bstörningar\b', r'\bdriftavbrott\b',
        r'\bkontakta\b', r'\bkundservice\b', r'\bjust\b', r'\bnu\b', r'\bhar\b', r'\bvi\b',
        r'\beftersom\b', r'\bprognos\b', r'\bsaknas\b'
    ]
    
    mismatches = []
    for oid, iid, desc_json in outages:
        if not desc_json: continue
        
        try:
            desc = json.loads(desc_json)
        except:
            continue
            
        en_desc = desc.get('en', '')
        if not en_desc: continue
        
        # Check if any Swedish indicator is in the English description
        is_swedish = any(re.search(ind, en_desc.lower()) for ind in sw_indicators)
        
        if is_swedish:
            mismatches.append({
                'id': oid,
                'incident_id': iid,
                'en': en_desc
            })
            
    print(f"Total Lycamobile outages checked: {len(outages)}")
    print(f"Total Swedish text in English descriptions found: {len(mismatches)}")
    
    if mismatches:
        print("\nFirst 10 examples:")
        for m in mismatches[:10]:
            print(f"ID: {m['id']} | Incident ID: {m['incident_id']}")
            print(f"EN Description: {m['en']}")
            print("-" * 20)

if __name__ == "__main__":
    check_swedish_descriptions()
