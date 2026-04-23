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

# Swedish county constants to avoid duplication
COUNTY_JONKOPINGS = "Jönköpings län"
COUNTY_VASTRA_GOTALANDS = "Västra Götalands län"
COUNTY_KRONOBERGS = "Kronobergs län"
COUNTY_VARMLANDS = "Värmlands län"
COUNTY_VASTMANLANDS = "Västmanlands län"
COUNTY_NORRBOTTENS = "Norrbottens län"
COUNTY_DALARNAS = "Dalarnas län"
COUNTY_JAMTLANDS = "Jämtlands län"
COUNTY_OREBRO = "Örebro län"
COUNTY_VASTERBOTTENS = "Västerbottens län"

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
    "Ale": COUNTY_VASTRA_GOTALANDS, "Alingsås": COUNTY_VASTRA_GOTALANDS, "Alvesta": COUNTY_KRONOBERGS, "Aneby": COUNTY_JONKOPINGS,
    "Arboga": COUNTY_VASTMANLANDS, "Arjeplog": COUNTY_NORRBOTTENS, "Arvidsjaur": COUNTY_NORRBOTTENS, "Arvika": COUNTY_VARMLANDS,
    "Askersund": COUNTY_OREBRO, "Avesta": COUNTY_DALARNAS, "Bengtsfors": COUNTY_VASTRA_GOTALANDS, "Berg": COUNTY_JAMTLANDS,
    "Bjurholm": COUNTY_VASTERBOTTENS, "Bjuv": "Skåne län", "Boden": COUNTY_NORRBOTTENS, "Bollebygd": COUNTY_VASTRA_GOTALANDS,
    "Bollnäs": "Gävleborgs län", "Borgholm": "Kalmar län", "Borlänge": COUNTY_DALARNAS, "Borås": COUNTY_VASTRA_GOTALANDS,
    "Botkyrka": "Stockholms län", "Boxholm": "Östergötlands län", "Bromölla": "Skåne län", "Bräcke": COUNTY_JAMTLANDS,
    "Burlöv": "Skåne län", "Båstad": "Skåne län", "Dals-Ed": COUNTY_VASTRA_GOTALANDS, "Danderyd": "Stockholms län",
    "Degerfors": COUNTY_OREBRO, "Dorotea": COUNTY_VASTERBOTTENS, "Eda": COUNTY_VARMLANDS, "Ekerö": "Stockholms län",
    "Eksjö": COUNTY_JONKOPINGS, "Emmaboda": "Kalmar län", "Enköping": "Uppsala län", "Eskilstuna": "Södermanlands län",
    "Eslöv": "Skåne län", "Essunga": COUNTY_VASTRA_GOTALANDS, "Fagersta": COUNTY_VASTMANLANDS, "Falkenberg": "Hallands län",
    "Falköping": COUNTY_VASTRA_GOTALANDS, "Falun": COUNTY_DALARNAS, "Filipstad": COUNTY_VARMLANDS, "Finspång": "Östergötlands län",
    "Flen": "Södermanlands län", "Forshaga": COUNTY_VARMLANDS, "Färgelanda": COUNTY_VASTRA_GOTALANDS, "Gagnef": COUNTY_DALARNAS,
    "Gislaved": COUNTY_JONKOPINGS, "Gnesta": "Södermanlands län", "Gnosjö": COUNTY_JONKOPINGS, "Gotland": "Gotlands län",
    "Grums": COUNTY_VARMLANDS, "Grästorp": COUNTY_VASTRA_GOTALANDS, "Gullspång": COUNTY_VASTRA_GOTALANDS, "Gällivare": COUNTY_NORRBOTTENS,
    "Gävle": "Gävleborgs län", "Göteborg": COUNTY_VASTRA_GOTALANDS, "Götene": COUNTY_VASTRA_GOTALANDS, "Habo": COUNTY_JONKOPINGS,
    "Hagfors": COUNTY_VARMLANDS, "Hallsberg": COUNTY_OREBRO, "Hallstahammar": COUNTY_VASTMANLANDS, "Halmstad": "Hallands län",
    "Hammarö": COUNTY_VARMLANDS, "Haninge": "Stockholms län", "Haparanda": COUNTY_NORRBOTTENS, "Heby": "Uppsala län",
    "Hedemora": COUNTY_DALARNAS, "Helsingborg": "Skåne län", "Herrljunga": COUNTY_VASTRA_GOTALANDS, "Hjo": COUNTY_VASTRA_GOTALANDS,
    "Hofors": "Gävleborgs län", "Huddinge": "Stockholms län", "Hudiksvall": "Gävleborgs län", "Hultsfred": "Kalmar län",
    "Hylte": "Hallands län", "Håbo": "Uppsala län", "Hällefors": COUNTY_OREBRO, "Härjedalen": COUNTY_JAMTLANDS,
    "Härnösand": "Västernorrlands län", "Härryda": COUNTY_VASTRA_GOTALANDS, "Hässleholm": "Skåne län", "Höganäs": "Skåne län",
    "Högsby": "Kalmar län", "Hörby": "Skåne län", "Höör": "Skåne län", "Jokkmokk": COUNTY_NORRBOTTENS, "Järfälla": "Stockholms län",
    "Jönköping": COUNTY_JONKOPINGS, "Kalix": COUNTY_NORRBOTTENS, "Kalmar": "Kalmar län", "Karlsborg": COUNTY_VASTRA_GOTALANDS,
    "Karlshamn": "Blekinge län", "Karlskoga": COUNTY_OREBRO, "Karlstad": COUNTY_VARMLANDS,
    "Katrineholm": "Södermanlands län", "Kil": COUNTY_VARMLANDS, "Kinda": "Östergötlands län", "Kiruna": COUNTY_NORRBOTTENS,
    "Klippan": "Skåne län", "Knivsta": "Uppsala län", "Kramfors": "Västernorrlands län", "Kristianstad": "Skåne län",
    "Kristinehamn": COUNTY_VARMLANDS, "Krokom": COUNTY_JAMTLANDS, "Kumla": COUNTY_OREBRO, "Kungsbacka": "Hallands län",
    "Kungsör": COUNTY_VASTMANLANDS, "Kungälv": COUNTY_VASTRA_GOTALANDS, "Kävlinge": "Skåne län", "Köping": COUNTY_VASTMANLANDS,
    "Laholm": "Hallands län", "Landskrona": "Skåne län", "Laxå": COUNTY_OREBRO, "Lekeberg": COUNTY_OREBRO, "Leksand": COUNTY_DALARNAS,
    "Lerum": COUNTY_VASTRA_GOTALANDS, "Lessebo": COUNTY_KRONOBERGS, "Lidingö": "Stockholms län", "Lidköping": COUNTY_VASTRA_GOTALANDS,
    "Lilla Edet": COUNTY_VASTRA_GOTALANDS, "Lindesberg": COUNTY_OREBRO, "Linköping": "Östergötlands län", "Ljungby": COUNTY_KRONOBERGS,
    "Ljusdal": "Gävleborgs län", "Ljusnarsberg": COUNTY_OREBRO, "Lomma": "Skåne län", "Ludvika": COUNTY_DALARNAS,
    "Luleå": COUNTY_NORRBOTTENS, "Lund": "Skåne län", "Lycksele": COUNTY_VASTERBOTTENS, "Lysekil": COUNTY_VASTRA_GOTALANDS,
    "Malå": COUNTY_VASTERBOTTENS, "Malmö": "Skåne län", "Mariestad": COUNTY_VASTRA_GOTALANDS, "Mark": COUNTY_VASTRA_GOTALANDS,
    "Markaryd": COUNTY_KRONOBERGS, "Mellerud": COUNTY_VASTRA_GOTALANDS, "Mjölby": "Östergötlands län", "Mora": COUNTY_DALARNAS,
    "Motala": "Östergötlands län", "Mullsjö": COUNTY_JONKOPINGS, "Munkedal": COUNTY_VASTRA_GOTALANDS, "Munkfors": COUNTY_VARMLANDS,
    "Mölndal": COUNTY_VASTRA_GOTALANDS, "Mönsterås": "Kalmar län", "Mörbylånga": "Kalmar län", "Nacka": "Stockholms län",
    "Nora": COUNTY_OREBRO, "Norberg": COUNTY_VASTMANLANDS, "Nordanstig": "Gävleborgs län", "Nordmaling": COUNTY_VASTERBOTTENS,
    "Norrköping": "Östergötlands län", "Norrtälje": "Stockholms län", "Norsjö": COUNTY_VASTERBOTTENS, "Nybro": "Kalmar län",
    "Nykvarn": "Stockholms län", "Nyköping": "Södermanlands län", "Nynäshamn": "Stockholms län", "Nässjö": COUNTY_JONKOPINGS,
    "Ockelbo": "Gävleborgs län", "Olofström": "Blekinge län", "Orsa": COUNTY_DALARNAS, "Orust": COUNTY_VASTRA_GOTALANDS,
    "Osby": "Skåne län", "Oskarshamn": "Kalmar län", "Ovanåker": "Gävleborgs län", "Oxelösund": "Södermanlands län",
    "Pajala": COUNTY_NORRBOTTENS, "Partille": COUNTY_VASTRA_GOTALANDS, "Perstorp": "Skåne län", "Piteå": COUNTY_NORRBOTTENS,
    "Ragunda": COUNTY_JAMTLANDS, "Robertsfors": COUNTY_VASTERBOTTENS, "Ronneby": "Blekinge län", "Rättvik": COUNTY_DALARNAS,
    "Sala": COUNTY_VASTMANLANDS, "Salem": "Stockholms län", "Sandviken": "Gävleborgs län", "Sigtuna": "Stockholms län",
    "Simrishamn": "Skåne län", "Sjöbo": "Skåne län", "Skara": COUNTY_VASTRA_GOTALANDS, "Skellefteå": COUNTY_VASTERBOTTENS,
    "Skinnskatteberg": COUNTY_VASTMANLANDS, "Skurup": "Skåne län", "Skövde": COUNTY_VASTRA_GOTALANDS, "Smedjebacken": COUNTY_DALARNAS,
    "Sollefteå": "Västernorrlands län", "Sollentuna": "Stockholms län", "Solna": "Stockholms län", "Sorsele": COUNTY_VASTERBOTTENS,
    "Sotenäs": COUNTY_VASTRA_GOTALANDS, "Staffanstorp": "Skåne län", "Stenungsund": COUNTY_VASTRA_GOTALANDS, "Stockholm": "Stockholms län",
    "Storfors": COUNTY_VARMLANDS, "Storuman": COUNTY_VASTERBOTTENS, "Strängnäs": "Södermanlands län", "Strömstad": COUNTY_VASTRA_GOTALANDS,
    "Strömsund": COUNTY_JAMTLANDS, "Sundbyberg": "Stockholms län", "Sundsvall": "Västernorrlands län", "Sunne": COUNTY_VARMLANDS,
    "Surahammar": COUNTY_VASTMANLANDS, "Svalöv": "Skåne län", "Svedala": "Skåne län", "Svenljunga": COUNTY_VASTRA_GOTALANDS,
    "Säffle": COUNTY_VARMLANDS, "Säter": COUNTY_DALARNAS, "Sävsjö": COUNTY_JONKOPINGS, "Söderhamn": "Gävleborgs län",
    "Söderköping": "Östergötlands län", "Södertälje": "Stockholms län", "Sölvesborg": "Blekinge län", "Tanum": COUNTY_VASTRA_GOTALANDS,
    "Tibro": COUNTY_VASTRA_GOTALANDS, "Tidaholm": COUNTY_VASTRA_GOTALANDS, "Tyresö": "Stockholms län", "Täby": "Stockholms län",
    "Töreboda": COUNTY_VASTRA_GOTALANDS, "Uddevalla": COUNTY_VASTRA_GOTALANDS, "Ulricehamn": COUNTY_VASTRA_GOTALANDS,
    "Umeå": COUNTY_VASTERBOTTENS, "Upplands-Bro": "Stockholms län", "Upplands Väsby": "Stockholms län", "Uppsala": "Uppsala län",
    "Uppvidinge": COUNTY_KRONOBERGS, "Vadstena": "Östergötlands län", "Vaggeryd": COUNTY_JONKOPINGS, "Valdemarsvik": "Östergötlands län",
    "Vallentuna": "Stockholms län", "Vansbro": COUNTY_DALARNAS, "Vara": COUNTY_VASTRA_GOTALANDS, "Varberg": "Hallands län",
    "Vaxholm": "Stockholms län", "Vellinge": "Skåne län", "Vetlanda": COUNTY_JONKOPINGS, "Vilhelmina": COUNTY_VASTERBOTTENS,
    "Vimmerby": "Kalmar län", "Vindeln": COUNTY_VASTERBOTTENS, "Vingåker": "Södermanlands län", "Vårgårda": COUNTY_VASTRA_GOTALANDS,
    "Vänersborg": COUNTY_VASTRA_GOTALANDS, "Vännäs": COUNTY_VASTERBOTTENS, "Värmdö": "Stockholms län", "Värnamo": COUNTY_JONKOPINGS,
    "Västervik": "Kalmar län", "Västerås": COUNTY_VASTMANLANDS, "Växjö": COUNTY_KRONOBERGS, "Ydre": "Östergötlands län",
    "Ystad": "Skåne län", "Åmål": COUNTY_VASTRA_GOTALANDS, "Ånge": "Västernorrlands län", "Åre": COUNTY_JAMTLANDS,
    "Årjäng": COUNTY_VARMLANDS, "Åsele": COUNTY_VASTERBOTTENS, "Åstorp": "Skåne län", "Åtvidaberg": "Östergötlands län",
    "Älmhult": COUNTY_KRONOBERGS, "Älvdalen": COUNTY_DALARNAS, "Älvkarleby": "Uppsala län", "Älvsbyn": COUNTY_NORRBOTTENS,
    "Ängelholm": "Skåne län", "Öckerö": COUNTY_VASTRA_GOTALANDS, "Ödeshög": "Östergötlands län", "Örebro": COUNTY_OREBRO,
    "Örkelljunga": "Skåne län", "Örnsköldsvik": "Västernorrlands län", "Östersund": COUNTY_JAMTLANDS, "Österåker": "Stockholms län",
    "Östhammar": "Uppsala län", "Östra Göinge": "Skåne län", "Överkalix": COUNTY_NORRBOTTENS, "Övertorneå": COUNTY_NORRBOTTENS,
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
