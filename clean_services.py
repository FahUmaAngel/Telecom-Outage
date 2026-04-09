import sqlite3
import json

def clean_services():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Fetch all INCSE incidents with affected_services
    cursor.execute("SELECT id, incident_id, affected_services FROM outages WHERE incident_id LIKE 'INCSE%'")
    rows = cursor.fetchall()
    
    updated_count = 0
    empty_services_incidents = []
    has_target_services = 0
    
    for row in rows:
        row_id, incident_id, services_json_str = row
        
        if not services_json_str:
            empty_services_incidents.append(incident_id)
            continue
            
        try:
            services_list = json.loads(services_json_str)
            if not isinstance(services_list, list):
                continue
                
            original_len = len(services_list)
            # Remove "voice" and "data" case-insensitively
            services_list = [s for s in services_list if s.lower() not in ('voice', 'data')]
            
            if len(services_list) < original_len:
                has_target_services += 1
                new_services_json = json.dumps(services_list, ensure_ascii=False)
                cursor.execute("UPDATE outages SET affected_services = ? WHERE id = ?", (new_services_json, row_id))
                updated_count += 1
            
            # Check if it's now completely empty
            if len(services_list) == 0:
                empty_services_incidents.append(incident_id)
                
        except json.JSONDecodeError:
            pass

    conn.commit()
    conn.close()
    
    # Remove duplicates from empty list, sort it
    empty_services_incidents = sorted(list(set(empty_services_incidents)))
    
    print("--------------------------------------------------")
    print(f"Total INCSE incidents modified (removed voice/data): {updated_count}")
    print(f"Total INCSE incidents that now have NO services at all: {len(empty_services_incidents)}")
    print("--------------------------------------------------")
    print("List of incidents with NO services:")
    for inc in empty_services_incidents:
        print(inc)
    print("--------------------------------------------------")

if __name__ == "__main__":
    clean_services()
