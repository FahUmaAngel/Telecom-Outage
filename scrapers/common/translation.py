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
COUNTY_SKANE = "Skåne län"
COUNTY_GAVLEBORGS = "Gävleborgs län"
COUNTY_KALMAR = "Kalmar län"
COUNTY_STOCKHOLMS = "Stockholms län"
COUNTY_OSTERGOTLANDS = "Östergötlands län"
COUNTY_SODERMANLANDS = "Södermanlands län"
COUNTY_UPPSALA = "Uppsala län"
COUNTY_HALLANDS = "Hallands län"
COUNTY_GOTLANDS = "Gotlands län"
COUNTY_VASTERNORRLANDS = "Västernorrlands län"
COUNTY_BLEKINGE = "Blekinge län"

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
    "Bjurholm": COUNTY_VASTERBOTTENS, "Bjuv": COUNTY_SKANE, "Boden": COUNTY_NORRBOTTENS, "Bollebygd": COUNTY_VASTRA_GOTALANDS,
    "Bollnäs": COUNTY_GAVLEBORGS, "Borgholm": COUNTY_KALMAR, "Borlänge": COUNTY_DALARNAS, "Borås": COUNTY_VASTRA_GOTALANDS,
    "Botkyrka": COUNTY_STOCKHOLMS, "Boxholm": COUNTY_OSTERGOTLANDS, "Bromölla": COUNTY_SKANE, "Bräcke": COUNTY_JAMTLANDS,
    "Burlöv": COUNTY_SKANE, "Båstad": COUNTY_SKANE, "Dals-Ed": COUNTY_VASTRA_GOTALANDS, "Danderyd": COUNTY_STOCKHOLMS,
    "Degerfors": COUNTY_OREBRO, "Dorotea": COUNTY_VASTERBOTTENS, "Eda": COUNTY_VARMLANDS, "Ekerö": COUNTY_STOCKHOLMS,
    "Eksjö": COUNTY_JONKOPINGS, "Emmaboda": COUNTY_KALMAR, "Enköping": COUNTY_UPPSALA, "Eskilstuna": COUNTY_SODERMANLANDS,
    "Eslöv": COUNTY_SKANE, "Essunga": COUNTY_VASTRA_GOTALANDS, "Fagersta": COUNTY_VASTMANLANDS, "Falkenberg": COUNTY_HALLANDS,
    "Falköping": COUNTY_VASTRA_GOTALANDS, "Falun": COUNTY_DALARNAS, "Filipstad": COUNTY_VARMLANDS, "Finspång": COUNTY_OSTERGOTLANDS,
    "Flen": COUNTY_SODERMANLANDS, "Forshaga": COUNTY_VARMLANDS, "Färgelanda": COUNTY_VASTRA_GOTALANDS, "Gagnef": COUNTY_DALARNAS,
    "Gislaved": COUNTY_JONKOPINGS, "Gnesta": COUNTY_SODERMANLANDS, "Gnosjö": COUNTY_JONKOPINGS, "Gotland": COUNTY_GOTLANDS,
    "Grums": COUNTY_VARMLANDS, "Grästorp": COUNTY_VASTRA_GOTALANDS, "Gullspång": COUNTY_VASTRA_GOTALANDS, "Gällivare": COUNTY_NORRBOTTENS,
    "Gävle": COUNTY_GAVLEBORGS, "Göteborg": COUNTY_VASTRA_GOTALANDS, "Götene": COUNTY_VASTRA_GOTALANDS, "Habo": COUNTY_JONKOPINGS,
    "Hagfors": COUNTY_VARMLANDS, "Hallsberg": COUNTY_OREBRO, "Hallstahammar": COUNTY_VASTMANLANDS, "Halmstad": COUNTY_HALLANDS,
    "Hammarö": COUNTY_VARMLANDS, "Haninge": COUNTY_STOCKHOLMS, "Haparanda": COUNTY_NORRBOTTENS, "Heby": COUNTY_UPPSALA,
    "Hedemora": COUNTY_DALARNAS, "Helsingborg": COUNTY_SKANE, "Herrljunga": COUNTY_VASTRA_GOTALANDS, "Hjo": COUNTY_VASTRA_GOTALANDS,
    "Hofors": COUNTY_GAVLEBORGS, "Huddinge": COUNTY_STOCKHOLMS, "Hudiksvall": COUNTY_GAVLEBORGS, "Hultsfred": COUNTY_KALMAR,
    "Hylte": COUNTY_HALLANDS, "Håbo": COUNTY_UPPSALA, "Hällefors": COUNTY_OREBRO, "Härjedalen": COUNTY_JAMTLANDS,
    "Härnösand": COUNTY_VASTERNORRLANDS, "Härryda": COUNTY_VASTRA_GOTALANDS, "Hässleholm": COUNTY_SKANE, "Höganäs": COUNTY_SKANE,
    "Högsby": COUNTY_KALMAR, "Hörby": COUNTY_SKANE, "Höör": COUNTY_SKANE, "Jokkmokk": COUNTY_NORRBOTTENS, "Järfälla": COUNTY_STOCKHOLMS,
    "Jönköping": COUNTY_JONKOPINGS, "Kalix": COUNTY_NORRBOTTENS, "Kalmar": COUNTY_KALMAR, "Karlsborg": COUNTY_VASTRA_GOTALANDS,
    "Karlshamn": COUNTY_BLEKINGE, "Karlskoga": COUNTY_OREBRO, "Karlstad": COUNTY_VARMLANDS,
    "Katrineholm": COUNTY_SODERMANLANDS, "Kil": COUNTY_VARMLANDS, "Kinda": COUNTY_OSTERGOTLANDS, "Kiruna": COUNTY_NORRBOTTENS,
    "Klippan": COUNTY_SKANE, "Knivsta": COUNTY_UPPSALA, "Kramfors": COUNTY_VASTERNORRLANDS, "Kristianstad": COUNTY_SKANE,
    "Kristinehamn": COUNTY_VARMLANDS, "Krokom": COUNTY_JAMTLANDS, "Kumla": COUNTY_OREBRO, "Kungsbacka": COUNTY_HALLANDS,
    "Kungsör": COUNTY_VASTMANLANDS, "Kungälv": COUNTY_VASTRA_GOTALANDS, "Kävlinge": COUNTY_SKANE, "Köping": COUNTY_VASTMANLANDS,
    "Laholm": COUNTY_HALLANDS, "Landskrona": COUNTY_SKANE, "Laxå": COUNTY_OREBRO, "Lekeberg": COUNTY_OREBRO, "Leksand": COUNTY_DALARNAS,
    "Lerum": COUNTY_VASTRA_GOTALANDS, "Lessebo": COUNTY_KRONOBERGS, "Lidingö": COUNTY_STOCKHOLMS, "Lidköping": COUNTY_VASTRA_GOTALANDS,
    "Lilla Edet": COUNTY_VASTRA_GOTALANDS, "Lindesberg": COUNTY_OREBRO, "Linköping": COUNTY_OSTERGOTLANDS, "Ljungby": COUNTY_KRONOBERGS,
    "Ljusdal": COUNTY_GAVLEBORGS, "Ljusnarsberg": COUNTY_OREBRO, "Lomma": COUNTY_SKANE, "Ludvika": COUNTY_DALARNAS,
    "Luleå": COUNTY_NORRBOTTENS, "Lund": COUNTY_SKANE, "Lycksele": COUNTY_VASTERBOTTENS, "Lysekil": COUNTY_VASTRA_GOTALANDS,
    "Malå": COUNTY_VASTERBOTTENS, "Malmö": COUNTY_SKANE, "Mariestad": COUNTY_VASTRA_GOTALANDS, "Mark": COUNTY_VASTRA_GOTALANDS,
    "Markaryd": COUNTY_KRONOBERGS, "Mellerud": COUNTY_VASTRA_GOTALANDS, "Mjölby": COUNTY_OSTERGOTLANDS, "Mora": COUNTY_DALARNAS,
    "Motala": COUNTY_OSTERGOTLANDS, "Mullsjö": COUNTY_JONKOPINGS, "Munkedal": COUNTY_VASTRA_GOTALANDS, "Munkfors": COUNTY_VARMLANDS,
    "Mölndal": COUNTY_VASTRA_GOTALANDS, "Mönsterås": COUNTY_KALMAR, "Mörbylånga": COUNTY_KALMAR, "Nacka": COUNTY_STOCKHOLMS,
    "Nora": COUNTY_OREBRO, "Norberg": COUNTY_VASTMANLANDS, "Nordanstig": COUNTY_GAVLEBORGS, "Nordmaling": COUNTY_VASTERBOTTENS,
    "Norrköping": COUNTY_OSTERGOTLANDS, "Norrtälje": COUNTY_STOCKHOLMS, "Norsjö": COUNTY_VASTERBOTTENS, "Nybro": COUNTY_KALMAR,
    "Nykvarn": COUNTY_STOCKHOLMS, "Nyköping": COUNTY_SODERMANLANDS, "Nynäshamn": COUNTY_STOCKHOLMS, "Nässjö": COUNTY_JONKOPINGS,
    "Ockelbo": COUNTY_GAVLEBORGS, "Olofström": COUNTY_BLEKINGE, "Orsa": COUNTY_DALARNAS, "Orust": COUNTY_VASTRA_GOTALANDS,
    "Osby": COUNTY_SKANE, "Oskarshamn": COUNTY_KALMAR, "Ovanåker": COUNTY_GAVLEBORGS, "Oxelösund": COUNTY_SODERMANLANDS,
    "Pajala": COUNTY_NORRBOTTENS, "Partille": COUNTY_VASTRA_GOTALANDS, "Perstorp": COUNTY_SKANE, "Piteå": COUNTY_NORRBOTTENS,
    "Ragunda": COUNTY_JAMTLANDS, "Robertsfors": COUNTY_VASTERBOTTENS, "Ronneby": COUNTY_BLEKINGE, "Rättvik": COUNTY_DALARNAS,
    "Sala": COUNTY_VASTMANLANDS, "Salem": COUNTY_STOCKHOLMS, "Sandviken": COUNTY_GAVLEBORGS, "Sigtuna": COUNTY_STOCKHOLMS,
    "Simrishamn": COUNTY_SKANE, "Sjöbo": COUNTY_SKANE, "Skara": COUNTY_VASTRA_GOTALANDS, "Skellefteå": COUNTY_VASTERBOTTENS,
    "Skinnskatteberg": COUNTY_VASTMANLANDS, "Skurup": COUNTY_SKANE, "Skövde": COUNTY_VASTRA_GOTALANDS, "Smedjebacken": COUNTY_DALARNAS,
    "Sollefteå": COUNTY_VASTERNORRLANDS, "Sollentuna": COUNTY_STOCKHOLMS, "Solna": COUNTY_STOCKHOLMS, "Sorsele": COUNTY_VASTERBOTTENS,
    "Sotenäs": COUNTY_VASTRA_GOTALANDS, "Staffanstorp": COUNTY_SKANE, "Stenungsund": COUNTY_VASTRA_GOTALANDS, "Stockholm": COUNTY_STOCKHOLMS,
    "Storfors": COUNTY_VARMLANDS, "Storuman": COUNTY_VASTERBOTTENS, "Strängnäs": COUNTY_SODERMANLANDS, "Strömstad": COUNTY_VASTRA_GOTALANDS,
    "Strömsund": COUNTY_JAMTLANDS, "Sundbyberg": COUNTY_STOCKHOLMS, "Sundsvall": COUNTY_VASTERNORRLANDS, "Sunne": COUNTY_VARMLANDS,
    "Surahammar": COUNTY_VASTMANLANDS, "Svalöv": COUNTY_SKANE, "Svedala": COUNTY_SKANE, "Svenljunga": COUNTY_VASTRA_GOTALANDS,
    "Säffle": COUNTY_VARMLANDS, "Säter": COUNTY_DALARNAS, "Sävsjö": COUNTY_JONKOPINGS, "Söderhamn": COUNTY_GAVLEBORGS,
    "Söderköping": COUNTY_OSTERGOTLANDS, "Södertälje": COUNTY_STOCKHOLMS, "Sölvesborg": COUNTY_BLEKINGE, "Tanum": COUNTY_VASTRA_GOTALANDS,
    "Tibro": COUNTY_VASTRA_GOTALANDS, "Tidaholm": COUNTY_VASTRA_GOTALANDS, "Tyresö": COUNTY_STOCKHOLMS, "Täby": COUNTY_STOCKHOLMS,
    "Töreboda": COUNTY_VASTRA_GOTALANDS, "Uddevalla": COUNTY_VASTRA_GOTALANDS, "Ulricehamn": COUNTY_VASTRA_GOTALANDS,
    "Umeå": COUNTY_VASTERBOTTENS, "Upplands-Bro": COUNTY_STOCKHOLMS, "Upplands Väsby": COUNTY_STOCKHOLMS, "Uppsala": COUNTY_UPPSALA,
    "Uppvidinge": COUNTY_KRONOBERGS, "Vadstena": COUNTY_OSTERGOTLANDS, "Vaggeryd": COUNTY_JONKOPINGS, "Valdemarsvik": COUNTY_OSTERGOTLANDS,
    "Vallentuna": COUNTY_STOCKHOLMS, "Vansbro": COUNTY_DALARNAS, "Vara": COUNTY_VASTRA_GOTALANDS, "Varberg": COUNTY_HALLANDS,
    "Vaxholm": COUNTY_STOCKHOLMS, "Vellinge": COUNTY_SKANE, "Vetlanda": COUNTY_JONKOPINGS, "Vilhelmina": COUNTY_VASTERBOTTENS,
    "Vimmerby": COUNTY_KALMAR, "Vindeln": COUNTY_VASTERBOTTENS, "Vingåker": COUNTY_SODERMANLANDS, "Vårgårda": COUNTY_VASTRA_GOTALANDS,
    "Vänersborg": COUNTY_VASTRA_GOTALANDS, "Vännäs": COUNTY_VASTERBOTTENS, "Värmdö": COUNTY_STOCKHOLMS, "Värnamo": COUNTY_JONKOPINGS,
    "Västervik": COUNTY_KALMAR, "Västerås": COUNTY_VASTMANLANDS, "Växjö": COUNTY_KRONOBERGS, "Ydre": COUNTY_OSTERGOTLANDS,
    "Ystad": COUNTY_SKANE, "Åmål": COUNTY_VASTRA_GOTALANDS, "Ånge": COUNTY_VASTERNORRLANDS, "Åre": COUNTY_JAMTLANDS,
    "Årjäng": COUNTY_VARMLANDS, "Åsele": COUNTY_VASTERBOTTENS, "Åstorp": COUNTY_SKANE, "Åtvidaberg": COUNTY_OSTERGOTLANDS,
    "Älmhult": COUNTY_KRONOBERGS, "Älvdalen": COUNTY_DALARNAS, "Älvkarleby": COUNTY_UPPSALA, "Älvsbyn": COUNTY_NORRBOTTENS,
    "Ängelholm": COUNTY_SKANE, "Öckerö": COUNTY_VASTRA_GOTALANDS, "Ödeshög": COUNTY_OSTERGOTLANDS, "Örebro": COUNTY_OREBRO,
    "Örkelljunga": COUNTY_SKANE, "Örnsköldsvik": COUNTY_VASTERNORRLANDS, "Östersund": COUNTY_JAMTLANDS, "Österåker": COUNTY_STOCKHOLMS,
    "Östhammar": COUNTY_UPPSALA, "Östra Göinge": COUNTY_SKANE, "Överkalix": COUNTY_NORRBOTTENS, "Övertorneå": COUNTY_NORRBOTTENS,
    "Visby": COUNTY_GOTLANDS, "Bromma": COUNTY_STOCKHOLMS, "Solna": COUNTY_STOCKHOLMS
}

# List of Swedish cities for general reference
SWEDISH_CITIES = list(CITY_TO_COUNTY.keys())

# Swedish counties (län)
SWEDISH_COUNTIES = [
    COUNTY_STOCKHOLMS, COUNTY_VASTRA_GOTALANDS, COUNTY_SKANE,
    COUNTY_UPPSALA, COUNTY_OSTERGOTLANDS, COUNTY_JONKOPINGS,
    COUNTY_KRONOBERGS, COUNTY_KALMAR, COUNTY_GOTLANDS,
    COUNTY_BLEKINGE, COUNTY_HALLANDS, COUNTY_VARMLANDS,
    COUNTY_OREBRO, COUNTY_VASTMANLANDS, COUNTY_DALARNAS,
    COUNTY_GAVLEBORGS, COUNTY_VASTERNORRLANDS, COUNTY_JAMTLANDS,
    COUNTY_VASTERBOTTENS, COUNTY_NORRBOTTENS, COUNTY_SODERMANLANDS
]
