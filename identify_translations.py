import sqlite3
import json
import re

def identify_swedish_in_english():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, incident_id, description FROM outages")
    rows = cursor.fetchall()
    
    swedish_keywords = [
        'just nu', 'driftsstörning', 'planerat arbete', 'klart', 'beräknas', 
        'påverkar', 'åtgärd', 'felsökning', 'pågår', 'vänligen', 'förstår',
        'avbrott', 'underhåll', 'tack för ditt tålamod'
    ]
    
    incidents_to_fix = []
    
    for row_id, inc_id, desc_json in rows:
        if not desc_json:
            continue
            
        try:
            desc_dict = json.loads(desc_json)
            sv_text = desc_dict.get('sv', '').lower()
            en_text = desc_dict.get('en', '').lower()
            
            if not en_text or en_text == sv_text:
                if any(keyword in sv_text for keyword in swedish_keywords):
                    incidents_to_fix.append((row_id, inc_id, desc_dict['sv']))
            elif any(keyword in en_text for keyword in swedish_keywords):
                incidents_to_fix.append((row_id, inc_id, desc_dict['sv']))
                
        except json.JSONDecodeError:
            continue
            
    conn.close()
    
    print(f"Found {len(incidents_to_fix)} incidents with potential Swedish text in English description.")
    for row_id, inc_id, sv_val in incidents_to_fix[:10]: # Preview first 10
        print(f"ID: {inc_id} | SV: {sv_val[:100]}...")
        
    # Save to a temp file for the next step
    with open('incidents_to_translate.json', 'w', encoding='utf-8') as f:
        json.dump(incidents_to_fix, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    identify_swedish_in_english()
