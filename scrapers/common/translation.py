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
    # Common templates (longer phrases first)
    "Under denna period kan man uppleva problem med täckningen i ovan område": "During this period, you may experience coverage issues in the above area",
    "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt": "We are currently experiencing a service disruption that may affect your services in the area. Our technicians are working to resolve it as soon as possible",
    "Just nu har vi driftstörningar i delar av norra Sverige pga rådande väder": "We are currently experiencing service disruptions in parts of northern Sweden due to the prevailing weather",
    "Just nu kan du uppleva störningar i mobilnätet som bland annat påverkar samtal, surf och andra mobila tjänster": "You may currently experience mobile network disruptions affecting calls, data, and other mobile services",
    "På grund av ett kabelfel i ditt område kan du uppleva störningar i mobilnätet som påverkar samtal, surf och andra mobila tjänster": "Due to a cable fault in your area, you may experience mobile network disruptions affecting calls, data, and other mobile services",
    "fault has been found, although it was resolved a long time ago and is considered obsolete": "A fault was found, but it has been resolved and is considered obsolete",
    
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
    "felsökning pågår": "troubleshooting in progress",
    "arbete pågår": "work in progress",
    "arbete startar": "work starts",
    "arbete klart": "work finished",
    "tekniker på väg": "technician on the way",
    "inget End date": "no end date",
    "beräknas vara klart": "estimated to be finished",
    "underhållsarbete": "maintenance work",
    "täckningen": "coverage",
    "pga": "due to",
    "rådande väder": "current weather",
    "ovan område": "above area",
    "norra sverige": "northern Sweden",
    "södra sverige": "southern Sweden",
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


# Swedish cities and their counties for better location extraction
CITY_TO_COUNTY = {
    "Ale": "Västra Götalands län", "Alingsås": "Västra Götalands län", "Alvesta": "Kronobergs län", "Aneby": "Jönköpings län",
    "Arboga": "Västmanlands län", "Arjeplog": "Norrbottens län", "Arvidsjaur": "Norrbottens län", "Arvika": "Värmlands län",
    "Askersund": "Örebro län", "Avesta": "Dalarnas län", "Bengtsfors": "Västra Götalands län", "Berg": "Jämtlands län",
    "Bjurholm": "Västerbottens län", "Bjuv": "Skåne län", "Boden": "Norrbottens län", "Bollebygd": "Västra Götalands län",
    "Bollnäs": "Gävleborgs län", "Borgholm": "Kalmar län", "Borlänge": "Dalarnas län", "Borås": "Västra Götalands län",
    "Botkyrka": "Stockholms län", "Boxholm": "Östergötlands län", "Bromölla": "Skåne län", "Bräcke": "Jämtlands län",
    "Burlöv": "Skåne län", "Båstad": "Skåne län", "Dals-Ed": "Västra Götalands län", "Danderyd": "Stockholms län",
    "Degerfors": "Örebro län", "Dorotea": "Västerbottens län", "Eda": "Värmlands län", "Ekerö": "Stockholms län",
    "Eksjö": "Jönköpings län", "Emmaboda": "Kalmar län", "Enköping": "Uppsala län", "Eskilstuna": "Södermanlands län",
    "Eslöv": "Skåne län", "Essunga": "Västra Götalands län", "Fagersta": "Västmanlands län", "Falkenberg": "Hallands län",
    "Falköping": "Västra Götalands län", "Falun": "Dalarnas län", "Filipstad": "Värmlands län", "Finspång": "Östergötlands län",
    "Flen": "Södermanlands län", "Forshaga": "Värmlands län", "Färgelanda": "Västra Götalands län", "Gagnef": "Dalarnas län",
    "Gislaved": "Jönköpings län", "Gnesta": "Södermanlands län", "Gnosjö": "Jönköpings län", "Gotland": "Gotlands län",
    "Grums": "Värmlands län", "Grästorp": "Västra Götalands län", "Gullspång": "Västra Götalands län", "Gällivare": "Norrbottens län",
    "Gävle": "Gävleborgs län", "Göteborg": "Västra Götalands län", "Götene": "Västra Götalands län", "Habo": "Jönköpings län",
    "Hagfors": "Värmlands län", "Hallsberg": "Örebro län", "Hallstahammar": "Västmanlands län", "Halmstad": "Hallands län",
    "Hammarö": "Värmlands län", "Haninge": "Stockholms län", "Haparanda": "Norrbottens län", "Heby": "Uppsala län",
    "Hedemora": "Dalarnas län", "Helsingborg": "Skåne län", "Herrljunga": "Västra Götalands län", "Hjo": "Västra Götalands län",
    "Hofors": "Gävleborgs län", "Huddinge": "Stockholms län", "Hudiksvall": "Gävleborgs län", "Hultsfred": "Kalmar län",
    "Hylte": "Hallands län", "Håbo": "Uppsala län", "Hällefors": "Örebro län", "Härjedalen": "Jämtlands län",
    "Härnösand": "Västernorrlands län", "Härryda": "Västra Götalands län", "Hässleholm": "Skåne län", "Höganäs": "Skåne län",
    "Högsby": "Kalmar län", "Hörby": "Skåne län", "Höör": "Skåne län", "Jokkmokk": "Norrbottens län", "Järfälla": "Stockholms län",
    "Jönköping": "Jönköpings län", "Kalix": "Norrbottens län", "Kalmar": "Kalmar län", "Karlsborg": "Västra Götalands län",
    "Karlshamn": "Blekinge län", "Karlskoga": "Örebro län", "Karlskrona": "Blekinge län", "Karlstad": "Värmlands län",
    "Katrineholm": "Södermanlands län", "Kil": "Värmlands län", "Kinda": "Östergötlands län", "Kiruna": "Norrbottens län",
    "Klippan": "Skåne län", "Knivsta": "Uppsala län", "Kramfors": "Västernorrlands län", "Kristianstad": "Skåne län",
    "Kristinehamn": "Värmlands län", "Krokom": "Jämtlands län", "Kumla": "Örebro län", "Kungsbacka": "Hallands län",
    "Kungsör": "Västmanlands län", "Kungälv": "Västra Götalands län", "Kävlinge": "Skåne län", "Köping": "Västmanlands län",
    "Laholm": "Hallands län", "Landskrona": "Skåne län", "Laxå": "Örebro län", "Lekeberg": "Örebro län", "Leksand": "Dalarnas län",
    "Lerum": "Västra Götalands län", "Lessebo": "Kronobergs län", "Lidingö": "Stockholms län", "Lidköping": "Västra Götalands län",
    "Lilla Edet": "Västra Götalands län", "Lindesberg": "Örebro län", "Linköping": "Östergötlands län", "Ljungby": "Kronobergs län",
    "Ljusdal": "Gävleborgs län", "Ljusnarsberg": "Örebro län", "Lomma": "Skåne län", "Ludvika": "Dalarnas län",
    "Luleå": "Norrbottens län", "Lund": "Skåne län", "Lycksele": "Västerbottens län", "Lysekil": "Västra Götalands län",
    "Malå": "Västerbottens län", "Malmö": "Skåne län", "Mariestad": "Västra Götalands län", "Mark": "Västra Götalands län",
    "Markaryd": "Kronobergs län", "Mellerud": "Västra Götalands län", "Mjölby": "Östergötlands län", "Mora": "Dalarnas län",
    "Motala": "Östergötlands län", "Mullsjö": "Jönköpings län", "Munkedal": "Västra Götalands län", "Munkfors": "Värmlands län",
    "Mölndal": "Västra Götalands län", "Mönsterås": "Kalmar län", "Mörbylånga": "Kalmar län", "Nacka": "Stockholms län",
    "Nora": "Örebro län", "Norberg": "Västmanlands län", "Nordanstig": "Gävleborgs län", "Nordmaling": "Västerbottens län",
    "Norrköping": "Östergötlands län", "Norrtälje": "Stockholms län", "Norsjö": "Västerbottens län", "Nybro": "Kalmar län",
    "Nykvarn": "Stockholms län", "Nyköping": "Södermanlands län", "Nynäshamn": "Stockholms län", "Nässjö": "Jönköpings län",
    "Ockelbo": "Gävleborgs län", "Olofström": "Blekinge län", "Orsa": "Dalarnas län", "Orust": "Västra Götalands län",
    "Osby": "Skåne län", "Oskarshamn": "Kalmar län", "Ovanåker": "Gävleborgs län", "Oxelösund": "Södermanlands län",
    "Pajala": "Norrbottens län", "Partille": "Västra Götalands län", "Perstorp": "Skåne län", "Piteå": "Norrbottens län",
    "Ragunda": "Jämtlands län", "Robertsfors": "Västerbottens län", "Ronneby": "Blekinge län", "Rättvik": "Dalarnas län",
    "Sala": "Västmanlands län", "Salem": "Stockholms län", "Sandviken": "Gävleborgs län", "Sigtuna": "Stockholms län",
    "Simrishamn": "Skåne län", "Sjöbo": "Skåne län", "Skara": "Västra Götalands län", "Skellefteå": "Västerbottens län",
    "Skinnskatteberg": "Västmanlands län", "Skurup": "Skåne län", "Skövde": "Västra Götalands län", "Smedjebacken": "Dalarnas län",
    "Sollefteå": "Västernorrlands län", "Sollentuna": "Stockholms län", "Solna": "Stockholms län", "Sorsele": "Västerbottens län",
    "Sotenäs": "Västra Götalands län", "Staffanstorp": "Skåne län", "Stenungsund": "Västra Götalands län", "Stockholm": "Stockholms län",
    "Storfors": "Värmlands län", "Storuman": "Västerbottens län", "Strängnäs": "Södermanlands län", "Strömstad": "Västra Götalands län",
    "Strömsund": "Jämtlands län", "Sundbyberg": "Stockholms län", "Sundsvall": "Västernorrlands län", "Sunne": "Värmlands län",
    "Surahammar": "Västmanlands län", "Svalöv": "Skåne län", "Svedala": "Skåne län", "Svenljunga": "Västra Götalands län",
    "Säffle": "Värmlands län", "Säter": "Dalarnas län", "Sävsjö": "Jönköpings län", "Söderhamn": "Gävleborgs län",
    "Söderköping": "Östergötlands län", "Södertälje": "Stockholms län", "Sölvesborg": "Blekinge län", "Tanum": "Västra Götalands län",
    "Tibro": "Västra Götalands län", "Tidaholm": "Västra Götalands län", "Tyresö": "Stockholms län", "Täby": "Stockholms län",
    "Töreboda": "Västra Götalands län", "Uddevalla": "Västra Götalands län", "Ulricehamn": "Västra Götalands län",
    "Umeå": "Västerbottens län", "Upplands-Bro": "Stockholms län", "Upplands Väsby": "Stockholms län", "Uppsala": "Uppsala län",
    "Uppvidinge": "Kronobergs län", "Vadstena": "Östergötlands län", "Vaggeryd": "Jönköpings län", "Valdemarsvik": "Östergötlands län",
    "Vallentuna": "Stockholms län", "Vansbro": "Dalarnas län", "Vara": "Västra Götalands län", "Varberg": "Hallands län",
    "Vaxholm": "Stockholms län", "Vellinge": "Skåne län", "Vetlanda": "Jönköpings län", "Vilhelmina": "Västerbottens län",
    "Vimmerby": "Kalmar län", "Vindeln": "Västerbottens län", "Vingåker": "Södermanlands län", "Vårgårda": "Västra Götalands län",
    "Vänersborg": "Västra Götalands län", "Vännäs": "Västerbottens län", "Värmdö": "Stockholms län", "Värnamo": "Jönköpings län",
    "Västervik": "Kalmar län", "Västerås": "Västmanlands län", "Växjö": "Kronobergs län", "Ydre": "Östergötlands län",
    "Ystad": "Skåne län", "Åmål": "Västra Götalands län", "Ånge": "Västernorrlands län", "Åre": "Jämtlands län",
    "Årjäng": "Värmlands län", "Åsele": "Västerbottens län", "Åstorp": "Skåne län", "Åtvidaberg": "Östergötlands län",
    "Älmhult": "Kronobergs län", "Älvdalen": "Dalarnas län", "Älvkarleby": "Uppsala län", "Älvsbyn": "Norrbottens län",
    "Ängelholm": "Skåne län", "Öckerö": "Västra Götalands län", "Ödeshög": "Östergötlands län", "Örebro": "Örebro län",
    "Örkelljunga": "Skåne län", "Örnsköldsvik": "Västernorrlands län", "Östersund": "Jämtlands län", "Österåker": "Stockholms län",
    "Östhammar": "Uppsala län", "Östra Göinge": "Skåne län", "Överkalix": "Norrbottens län", "Övertorneå": "Norrbottens län",
    "Visby": "Gotlands län", "Bromma": "Stockholms län", "Solna": "Stockholms län"
}

# List of Swedish cities for general reference
SWEDISH_CITIES = list(CITY_TO_COUNTY.keys())

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
