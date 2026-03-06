from geopy.geocoders import Nominatim
from openlocationcode import openlocationcode as olc
import re

def resolve_place(query: str):
    """
    Resolves a place string (Plus Code or Address) to coordinates and a display name (Region).
    """
    geolocator = Nominatim(user_agent="telecom_outage_admin")
    lat, lon = None, None
    display_name = None
    county = None

    # 1. Check if it's a Plus Code (e.g., M2GM+R6 Göteborg)
    plus_code_match = re.search(r'([23456789CFGHJMPQRVWX]{2,8}\+[23456789CFGHJMPQRVWX]{2,})', query)
    
    if plus_code_match:
        code = plus_code_match.group(1)
        try:
            if olc.isFull(code):
                decoded = olc.decode(code)
                lat, lon = decoded.latitudeCenter, decoded.longitudeCenter
            else:
                # Short code, use the rest of the string as hint
                rest_of_query = query.replace(code, '').strip(', ')
                location = geolocator.geocode(rest_of_query)
                if location:
                    recovered = olc.recoverNearest(code, location.latitude, location.longitude)
                    decoded = olc.decode(recovered)
                    lat, lon = decoded.latitudeCenter, decoded.longitudeCenter
        except Exception as e:
            print(f"Plus code resolution failed: {e}")

        # If we have lat/lon from Plus Code, Reverse Geocode to get address details
        if lat and lon:
            try:
                # Reverse geocoding to get the county (region)
                location_reverse = geolocator.reverse((lat, lon), addressdetails=True, language="sv")
                if location_reverse:
                    address = location_reverse.raw.get('address', {})
                    # In Sweden, 'county' corresponds to the "Län" (Region)
                    county = address.get('county') or address.get('state')
            except Exception as e:
                print(f"Reverse geocoding failed: {e}")

    # 2. Fallback to standard geocoding
    if not lat or not lon:
        try:
            location = geolocator.geocode(query, addressdetails=True, language="sv")
            if location:
                lat, lon = location.latitude, location.longitude
                address = location.raw.get('address', {})
                county = address.get('county') or address.get('state')
        except Exception as e:
            print(f"Geocoding failed: {e}")

    if lat and lon:
        return {
            "latitude": lat,
            "longitude": lon,
            "display_name": county or query, # Use the county/region name by default
            "county": county
        }

    return None
