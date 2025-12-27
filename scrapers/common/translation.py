# Translation utilities for Swedish to English
# Supports bilingual website (Swedish-English)

SWEDISH_TO_ENGLISH = {
    # Outage types
    "störning": "disruption",
    "avbrott": "outage",
    "planerat avbrott": "planned outage",
    "oplanerat avbrott": "unplanned outage",
    "driftstörning": "service disruption",
    "fel": "fault",
    "kabelfel": "cable fault",
    
    # Network types
    "mobilnät": "mobile network",
    "mobila nätet": "mobile network",
    "fasta nätet": "fixed network",
    "bredband": "broadband",
    "fiber": "fiber",
    "telefoni": "telephony",
    
    # Status
    "aktiv": "active",
    "löst": "resolved",
    "pågående": "ongoing",
    "undersökning": "investigating",
    "åtgärdas": "being fixed",
    "planerad": "scheduled",
    
    # Severity
    "allvarlig": "severe",
    "omfattande": "extensive",
    "stor": "major",
    "liten": "minor",
    "begränsad": "limited",
    "lokal": "local",
    
    # Services
    "4G": "4G",
    "5G": "5G",
    "LTE": "LTE",
    "3G": "3G",
    "2G": "2G",
    "surf": "data",
    "samtal": "calls",
    "sms": "SMS",
    "mms": "MMS",
    
    # Locations
    "län": "county",
    "kommun": "municipality",
    "område": "area",
    "region": "region",
    "plats": "location",
    
    # Time
    "beräknad åtgärdstid": "estimated fix time",
    "starttid": "start time",
    "sluttid": "end time",
    
    # Common phrases
    "på grund av": "due to",
    "kan du uppleva": "you may experience",
    "vi arbetar med att": "we are working to",
    "åtgärda": "fix",
    "felet": "the fault",
    "i ditt område": "in your area",
}

def translate_swedish_to_english(text: str) -> str:
    """
    Translate Swedish text to English using dictionary lookup.
    
    Args:
        text: Swedish text to translate
        
    Returns:
        English translation (best effort)
    """
    if not text:
        return ""
    
    translated = text.lower()
    
    # Replace known phrases (longer phrases first)
    sorted_phrases = sorted(SWEDISH_TO_ENGLISH.items(), 
                           key=lambda x: len(x[0]), 
                           reverse=True)
    
    for swedish, english in sorted_phrases:
        translated = translated.replace(swedish.lower(), english)
    
    return translated


def create_bilingual_text(swedish: str, english: str = None) -> dict:
    """
    Create bilingual text object for API responses.
    
    Args:
        swedish: Swedish text
        english: English translation (auto-translated if not provided)
        
    Returns:
        Dictionary with both languages
    """
    if english is None:
        english = translate_swedish_to_english(swedish)
    
    return {
        "sv": swedish,
        "en": english
    }


# Swedish city names (for location extraction)
SWEDISH_CITIES = [
    "Stockholm", "Göteborg", "Malmö", "Uppsala", "Västerås",
    "Örebro", "Linköping", "Helsingborg", "Jönköping", "Norrköping",
    "Lund", "Umeå", "Gävle", "Borås", "Södertälje", "Eskilstuna",
    "Karlstad", "Täby", "Växjö", "Halmstad", "Sundsvall", "Luleå",
    "Trollhättan", "Östersund", "Borlänge", "Falun", "Kalmar",
    "Kristianstad", "Karlskrona", "Skellefteå", "Uddevalla", "Skövde"
]

# Swedish counties (län)
SWEDISH_COUNTIES = [
    "Stockholms län", "Västra Götalands län", "Skåne län",
    "Uppsala län", "Östergötlands län", "Jönköpings län",
    "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Hallands län", "Värmlands län",
    "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län", "Södermanlands län"
]
