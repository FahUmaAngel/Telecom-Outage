import sqlite3
import json
import os
import sys

# Move to the project root to import common modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

def deep_repair_lyca():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    query = """
    SELECT o.id, o.incident_id, o.title, o.description, o.location
    FROM outages o
    JOIN operators op ON o.operator_id = op.id
    WHERE op.name = 'lycamobile' 
    AND o.location IN ('Sverige', 'Unknown', 'unknown', 'sverige')
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Analyzing {len(rows)} bad Lyca records...")
    
    fixed = 0
    for r in rows:
        db_id, inc_id, title_json, desc_json, old_loc = r
        
        try:
            title = json.loads(title_json).get('sv', '') if title_json else ''
            desc = json.loads(desc_json).get('sv', '') if desc_json else ''
        except:
            title = str(title_json)
            desc = str(desc_json)
            
        full_text = f"{title} {desc}"
        new_loc = extract_region_from_text(full_text, SWEDISH_COUNTIES)
        
        if new_loc and new_loc != "Unknown":
            print(f"Found Match! ID:{inc_id} -> {new_loc} (Text: {full_text[:50]}...)")
            cursor.execute("UPDATE outages SET location = ? WHERE id = ?", (new_loc, db_id))
            fixed += 1
        else:
            # Print a few that aren't matching to see if we can manually spot patterns
            if fixed < 5:
                 pass
            # Let's print the first 5 failures
            if rows.index(r) < 5:
                print(f"No Match ID:{inc_id} - Title: {title} - Desc: {desc}")

    conn.commit()
    print(f"Repaired {fixed} more Lycamobile records.")
    conn.close()

if __name__ == '__main__':
    deep_repair_lyca()
