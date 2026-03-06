import sqlite3
import json

# Full mapping for high-quality translations as requested by user
TRANSLATION_MAP = {
    # 1. Preferred phrasing for common Telia outage message
    "We are currently experiencing an outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible.":
        "We are currently experiencing an outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible.",
    
    # 2. Network disruptions
    "Right now, you may experience disruptions in the mobile network that affect calls, browsing and other mobile services.":
        "Right now, you may experience disruptions in the mobile network that affect calls, browsing and other mobile services.",
        
    # 3. Cable fault
    "Due to a cable fault in your area, you may experience disruptions to the mobile network affecting calls, browsing and other mobile services.":
        "Due to a cable fault in your area, you may experience disruptions to the mobile network affecting calls, browsing and other mobile services.",
        
    # 4. Visby area
    "Historical disturbance registered for the Visby area. Affecting mobile network services.":
        "Historical disturbance registered for the Visby area. Affecting mobile network services.",
        
    # 5. Eskilstuna area
    "Network disruption affecting regional services in the Eskilstuna area.":
        "Network disruption affecting regional services in the Eskilstuna area.",
        
    # 6. Sölvesborg area
    "Active interference in Sölvesborg. Reduced capacity for mobile services.":
        "Active interference in Sölvesborg. Reduced capacity for mobile services.",
        
    # 7. Västra Götaland region
    "Disruption affecting the mobile network in the Västra Götaland region.":
        "Disruption affecting the mobile network in the Västra Götaland region.",

    # Swedish to New English (mappings for direct translation)
    "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.":
        "We are currently experiencing an outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible.",
    
    "Just nu kan du uppleva störningar i mobilnätet som bland annat påverkar samtal, surf och andra mobila tjänster.":
        "Right now, you may experience disruptions in the mobile network that affect calls, browsing and other mobile services.",
        
    "På grund av ett kabelfel i ditt område kan du uppleva störningar i mobilnätet som påverkar samtal, surf och andra mobila tjänster.":
        "Due to a cable fault in your area, you may experience disruptions to the mobile network affecting calls, browsing and other mobile services.",
        
    "Historisk störning registrerad för Visbytrakten. Påverkar mobilnätets tjänster.":
        "Historical disturbance registered for the Visby area. Affecting mobile network services.",
        
    "Nätverksstörning som påverkar regionala tjänster i Eskilstunaområdet.":
        "Network disruption affecting regional services in the Eskilstuna area.",
        
    "Aktiv störning i Sölvesborg. Reducerad kapacitet för mobila tjänster.":
        "Active interference in Sölvesborg. Reduced capacity for mobile services.",
        
    "Driftstörning som påverkar mobilnätet i Västra Götalands regionen.":
        "Disruption affecting the mobile network in the Västra Götaland region.",
}

def fix_all_translations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, description FROM outages WHERE description IS NOT NULL")
    rows = cursor.fetchall()
    
    updates = 0
    print(f"Checking {len(rows)} incidents for translation fixes...")
    
    for row_id, desc_json in rows:
        try:
            desc_dict = json.loads(desc_json)
            en_orig = desc_dict.get('en', '')
            sv_orig = desc_dict.get('sv', '')
            
            # Apply translations to BOTH sv->en and en-fixed->en-preferred
            new_en = en_orig
            
            # Check if English contains Swedish segments
            for sv_seg, en_fix in [("en driftstörning som kan påverka dina tjänster i området", "an outage that may affect your services in the area"), 
                                 ("tekniker jobbar på att lösa det så snart som möjligt", "technicians are working to resolve it as soon as possible")]:
                 if sv_seg in en_orig:
                     new_en = new_en.replace(sv_seg, en_fix)
            
            # Application of the map
            changed = False
            for old, preferred in TRANSLATION_MAP.items():
                if old in new_en:
                    new_en = new_en.replace(old, preferred)
                    changed = True
                
                # Also check to see if we can translate from Swedish directly if it was missed
                if old in sv_orig and (not en_orig or any(kw in en_orig.lower() for kw in ['driftstörning', 'tekniker'])):
                    new_en = preferred
                    changed = True
            
            if new_en != en_orig:
                desc_dict['en'] = new_en
                cursor.execute("UPDATE outages SET description = ? WHERE id = ?", (json.dumps(desc_dict, ensure_ascii=False), row_id))
                updates += 1
                
        except:
            continue
            
    conn.commit()
    conn.close()
    print(f"Successfully applied fixes to {updates} incidents.")

if __name__ == "__main__":
    fix_all_translations()
