"""
Tre mapper.
"""
from typing import List, Dict, Optional
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.common.models import (
    NormalizedOutage,
    OperatorEnum,
    SeverityLevel,
    OutageStatus,
    ServiceType
)
from scrapers.common.translation import translate_swedish_to_english, SWEDISH_COUNTIES
from scrapers.common.engine import classify_services, extract_region_from_text
import requests
import time

logger = logging.getLogger(__name__)

def determine_title_and_status(location: str, desc_sv: str):
    if "Driftstörning" in location:
         title_sv = location
         title_en = f"Service disruption in {location.replace('Driftstörning i ', '')}"
         status = OutageStatus.ACTIVE
    elif "driftstörning" in desc_sv.lower():
         title_sv = f"Driftstörning i {location}"
         title_en = f"Service disruption in {location}"
         status = OutageStatus.ACTIVE
    else:
         title_sv = f"Planerat arbete i {location}"
         title_en = f"Planned maintenance in {location}"
         status = OutageStatus.SCHEDULED
    return title_sv, title_en, status

def get_county_from_nominatim(location: str) -> Optional[str]:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': f"{location}, Sweden", 'format': 'json', 'addressdetails': 1, 'limit': 1}
        headers = {'User-Agent': 'TelecomOutageBot/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                addr = data[0].get('address', {})
                resolved_county = addr.get('county')
                if resolved_county:
                    return extract_region_from_text(resolved_county, SWEDISH_COUNTIES) or resolved_county
        time.sleep(1) # respectful rate limit
    except requests.RequestException:
        pass
    except ValueError:
        pass
    return None

def determine_county(location: str, title_sv: str, desc_sv: str) -> Optional[str]:
    lookup_text = f"{location} {title_sv} {desc_sv}"
    county_name = extract_region_from_text(lookup_text, SWEDISH_COUNTIES)
    
    if not county_name and location.lower() not in ['sverige', 'hela sverige']:
        county_name = get_county_from_nominatim(location)
        
    return county_name

def map_to_normalized(parsed_outage: Dict) -> Optional[NormalizedOutage]:
    try:
        desc_sv = parsed_outage.get('description', '')
        desc_en = translate_swedish_to_english(desc_sv)
        location = parsed_outage.get('location', 'Sverige')
        
        title_sv, _, status = determine_title_and_status(location, desc_sv)
        
        context_text = f"{location} {desc_sv} {title_sv}"
        affected_services = classify_services(context_text)

        # Keep only the standardized mobile-generation service enums used by the schema.
        allowed_services = {
            ServiceType.MOBILE_5G_PLUS,
            ServiceType.MOBILE_5G,
            ServiceType.MOBILE_4G,
            ServiceType.MOBILE_3G,
            ServiceType.MOBILE_2G,
            ServiceType.MOBILE,
        }
        affected_services = [service for service in affected_services if service in allowed_services]
        
        inc_id = parsed_outage.get('id')
        
        county_name = determine_county(location, title_sv, desc_sv)
        
        if not county_name:
            logger.info(f"Dropping Tre outage {inc_id} because it lacks a strict Region mapping (Loc: {location})")
            return None
            
        normalized = NormalizedOutage(
            operator=OperatorEnum.TRE,
            incident_id=inc_id,
            title={
                'sv': inc_id,
                'en': inc_id
            },
            description={
                'sv': desc_sv,
                'en': desc_en
            },
            status=status,
            affected_services=affected_services,
            location=county_name,
            estimated_fix_time=parsed_outage.get('end_time'),
            started_at=parsed_outage.get('start_time')
        )
        return normalized
        
    except Exception as e:
        logger.exception(f"Error mapping Tre: {e}")
        return None

def map_tre_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    normalized_outages = []
    for parsed_outage in parsed_outages:
        normalized = map_to_normalized(parsed_outage)
        if normalized:
            normalized_outages.append(normalized)
    return normalized_outages
