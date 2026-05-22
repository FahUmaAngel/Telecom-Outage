import re

def _get_geolocator():
    from geopy.geocoders import Nominatim
    return Nominatim(user_agent="telecom_outage_admin")

def _get_open_location_code():
    from openlocationcode import openlocationcode as olc
    return olc

def resolve_place(query: str):
    """
    Resolves a place string (Plus Code or Address) to coordinates and a display name (Region).
    Returns at minimum lat/lon if geopy is unavailable but a full Plus Code is provided.
    """
    geopy_available = True
    try:
        _get_geolocator()
    except ModuleNotFoundError:
        geopy_available = False

    # Try Plus Code resolution first (works without geopy for full codes)
    try:
        plus_code_result = _resolve_plus_code(query, geopy_available=geopy_available)
    except ModuleNotFoundError:
        plus_code_result = None
    if plus_code_result:
        return plus_code_result

    if not geopy_available:
        return None

    # Fallback to standard geocoding
    return _resolve_geocoding(query)


def _resolve_plus_code(query: str, geopy_available: bool = True):
    """
    Attempt to resolve a Plus Code to coordinates and region information.
    Returns a dict with latitude, longitude, display_name, and county if successful, None otherwise.
    When geopy_available=False, returns coordinates only (no reverse geocoding).
    """
    olc = _get_open_location_code()

    # 1. Check if it's a Plus Code (e.g., M2GM+R6 Göteborg)
    plus_code_match = re.search(r'([23456789CFGHJMPQRVWX]{2,8}\+[23456789CFGHJMPQRVWX]{2,})', query)

    if not plus_code_match:
        return None

    code = plus_code_match.group(1)

    try:
        if olc.isFull(code):
            decoded = olc.decode(code)
            lat, lon = decoded.latitudeCenter, decoded.longitudeCenter
        elif geopy_available:
            # Short code needs a reference location — requires geopy
            geolocator = _get_geolocator()
            rest_of_query = query.replace(code, '').strip(', ')
            location = geolocator.geocode(rest_of_query)
            if not location:
                return None
            recovered = olc.recoverNearest(code, location.latitude, location.longitude)
            decoded = olc.decode(recovered)
            lat, lon = decoded.latitudeCenter, decoded.longitudeCenter
        else:
            return None
    except Exception as e:
        print(f"Plus code resolution failed: {e}")
        return None

    # Return coordinates-only if geopy unavailable (no reverse geocoding)
    if not geopy_available:
        return {"latitude": lat, "longitude": lon, "display_name": None, "county": None}

    # Reverse geocode to get the county (region)
    if lat and lon:
        try:
            geolocator = _get_geolocator()
            location_reverse = geolocator.reverse((lat, lon), addressdetails=True, language="sv")
            if location_reverse:
                address = location_reverse.raw.get('address', {})
                county = address.get('county') or address.get('state')
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "display_name": county or query,
                    "county": county
                }
        except Exception as e:
            print(f"Reverse geocoding failed: {e}")
            return {
                "latitude": lat,
                "longitude": lon,
                "display_name": query,
                "county": None
            }
    
    return None


def _resolve_geocoding(query: str):
    """
    Attempt to resolve a standard address query to coordinates and region information.
    Returns a dict with latitude, longitude, display_name, and county if successful, None otherwise.
    """
    geolocator = _get_geolocator()
    
    try:
        location = geolocator.geocode(query, addressdetails=True, language="sv")
        if location:
            lat, lon = location.latitude, location.longitude
            address = location.raw.get('address', {})
            county = address.get('county') or address.get('state')
            return {
                "latitude": lat,
                "longitude": lon,
                "display_name": county or query,
                "county": county
            }
    except Exception as e:
        print(f"Geocoding failed: {e}")
    
    return None
