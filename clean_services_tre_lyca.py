import sqlite3
import json

def clean_services_by_operator():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Fetch incidents for 'tre' and 'lycamobile'
    cursor.execute("""
        SELECT o.id, o.incident_id, o.affected_services, op.name 
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name IN ('tre', 'lycamobile')
    """)
    rows = cursor.fetchall()
    
    updated_count = 0
    empty_services_incidents = []
    
    for row in rows:
        row_id, incident_id, services_json_str, operator_name = row
        
        # Some incidents might not have a public incident_id string, use ID as fallback for logging
        display_id = incident_id if incident_id else f"DB_ID_{row_id}"
        
        if not services_json_str:
            empty_services_incidents.append(display_id)
            continue
            
        try:
            services_list = json.loads(services_json_str)
            if not isinstance(services_list, list):
                continue
                
            original_len = len(services_list)
            # Remove "voice" and "data" case-insensitively
            services_list = [s for s in services_list if s.lower() not in ('voice', 'data')]
            
            if len(services_list) < original_len:
                new_services_json = json.dumps(services_list, ensure_ascii=False)
                cursor.execute("UPDATE outages SET affected_services = ? WHERE id = ?", (new_services_json, row_id))
                updated_count += 1
            
            # Check if it's now completely empty
            if len(services_list) == 0:
                empty_services_incidents.append(display_id)
                
        except json.JSONDecodeError:
            pass

    conn.commit()
    conn.close()
    
    # Remove duplicates from empty list
    empty_services_incidents = sorted(list(set(empty_services_incidents)))
    
    print("--------------------------------------------------")
    print(f"Total 'tre' and 'lycamobile' incidents modified (removed voice/data): {updated_count}")
    print(f"Total 'tre' and 'lycamobile' incidents that now have NO services at all: {len(empty_services_incidents)}")
    print("--------------------------------------------------")
    print("List of these incidents with NO services:")
    for inc in empty_services_incidents:
        print(inc)
    print("--------------------------------------------------")

if __name__ == "__main__":
    clean_services_by_operator()
