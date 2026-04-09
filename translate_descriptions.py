import sqlite3
import json
import time

# Simple translation mapping for frequently occurring Swedish phrases
TRANSLATION_MAP = {
    # 1. Preferred phrasing for common Telia outage message
    "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.":
        "We are currently experiencing an outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible.",
    
    # 2. Network disruptions
    "Just nu kan du uppleva störningar i mobilnätet som bland annat påverkar samtal, surf och andra mobila tjänster.":
        "Right now, you may experience disruptions in the mobile network that affect calls, browsing and other mobile services.",
        
    # 3. Cable fault
    "På grund av ett kabelfel i ditt område kan du uppleva störningar i mobilnätet som påverkar samtal, surf och andra mobila tjänster.":
        "Due to a cable fault in your area, you may experience disruptions to the mobile network affecting calls, browsing and other mobile services.",
        
    # 4. Visby area
    "Historisk störning registrerad för Visbytrakten. Påverkar mobilnätets tjänster.":
        "Historical disturbance registered for the Visby area. Affecting mobile network services.",
        
    # 5. Eskilstuna area
    "Nätverksstörning som påverkar regionala tjänster i Eskilstunaområdet.":
        "Network disruption affecting regional services in the Eskilstuna area.",
        
    # 6. Sölvesborg area
    "Aktiv störning i Sölvesborg. Reducerad kapacitet för mobila tjänster.":
        "Active interference in Sölvesborg. Reduced capacity for mobile services.",
        
    # 7. Västra Götaland region
    "Driftstörning som påverkar mobilnätet i Västra Götalands regionen.":
        "Disruption affecting the mobile network in the Västra Götaland region.",

    # Fallback and common phrases
    "Felsökning pågår": "Troubleshooting in progress",
    "Planerat arbete": "Planned maintenance",
    "Driftstörning": "Service disruption",
    "Beräknas klart": "Estimated completion",
    "Vi arbetar för att lösa problemet så snart som möjligt.": 
        "We are working to resolve the issue as soon as possible.",
    "Tack för ditt tålamod.": "Thank you for your patience.",
    "senast": "at the latest",
    "Vi beklagar detta och jobbar på en lösning.": 
        "We apologize for this and are working on a solution."
}

def translate_and_update():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Reload fresh list (will check for any descriptions where English contains Swedish keywords)
    import subprocess
    subprocess.run(["python", "identify_translations.py"], capture_output=True)

    with open('incidents_to_translate.json', 'r', encoding='utf-8') as f:
        incidents = json.load(f)
        
    print(f"Starting translation for {len(incidents)} incidents...")
    
    updates = 0
    for row_id, inc_id, sv_text in incidents:
        # Check if we have a direct translation or if it contains multiple common phrases
        en_translation = sv_text
        for sv_phrase, en_phrase in TRANSLATION_MAP.items():
            en_translation = en_translation.replace(sv_phrase, en_phrase)
        
        # If no translation was made (it didn't match anything in our map), 
        # for this exercise we'll just skip or do a very basic one.
        # However, many follow the same common Telia patterns.
        
        if en_translation != sv_text:
            cursor.execute("SELECT description FROM outages WHERE id = ?", (row_id,))
            current_desc_json = cursor.fetchone()[0]
            
            try:
                desc_dict = json.loads(current_desc_json)
                desc_dict['en'] = en_translation
                new_desc_json = json.dumps(desc_dict, ensure_ascii=False)
                
                cursor.execute("UPDATE outages SET description = ? WHERE id = ?", (new_desc_json, row_id))
                updates += 1
            except:
                continue
                
    conn.commit()
    conn.close()
    print(f"Successfully updated {updates} incidents with English translations.")

if __name__ == "__main__":
    translate_and_update()
