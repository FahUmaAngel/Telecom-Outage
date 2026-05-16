import sqlite3, json

def audit_lyca():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query for Lycamobile incidents with the 'Sverige' coordinates
    query = """
        SELECT o.incident_id, rd.data 
        FROM outages o 
        JOIN raw_data rd ON o.raw_data_id = rd.id 
        JOIN operators op ON o.operator_id = op.id 
        WHERE op.name = 'lycamobile' 
          AND o.latitude BETWEEN 59.67 AND 59.68 
          AND o.longitude BETWEEN 14.52 AND 14.53
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    results = {}
    for inc_id, raw_json in rows:
        try:
            data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
            results[inc_id] = data
        except (json.JSONDecodeError, TypeError):
            results[inc_id] = "Error parsing"
            
    with open('lyca_raw_audit_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Audit complete. Processed {len(rows)} incidents. Results saved to lyca_raw_audit_results.json")
    conn.close()

if __name__ == "__main__":
    audit_lyca()
