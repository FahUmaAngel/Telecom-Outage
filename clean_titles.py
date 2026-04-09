import sqlite3
import json
import re

def clean_incident_titles():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # We fetch all incidents to inspect their JSON titles
    cursor.execute("SELECT id, incident_id, title FROM outages WHERE incident_id LIKE 'INCSE%'")
    rows = cursor.fetchall()
    
    updates = 0
    
    for row in rows:
        row_id, incident_id, title_json_str = row
        if not title_json_str:
            continue
            
        try:
            title_dict = json.loads(title_json_str)
            needs_update = False
            
            for lang in ['sv', 'en']:
                if lang in title_dict and title_dict[lang]:
                    # Check if title strictly starts with the incident_id
                    if title_dict[lang].startswith(incident_id):
                        title_dict[lang] = incident_id
                        needs_update = True
            
            if needs_update:
                new_title_json = json.dumps(title_dict, ensure_ascii=False)
                cursor.execute("UPDATE outages SET title = ? WHERE id = ?", (new_title_json, row_id))
                updates += 1
                
        except json.JSONDecodeError:
            pass

    conn.commit()
    conn.close()
    
    print(f"Successfully cleaned up {updates} incident titles that contained extra text.")

if __name__ == "__main__":
    clean_incident_titles()
