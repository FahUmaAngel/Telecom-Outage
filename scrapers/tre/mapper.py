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
from scrapers.common.translation import translate_swedish_to_english

logger = logging.getLogger(__name__)

def map_to_normalized(parsed_outage: Dict) -> Optional[NormalizedOutage]:
    try:
        desc_sv = parsed_outage.get('description', '')
        desc_en = translate_swedish_to_english(desc_sv)
        
        # Determine title and status
        location = parsed_outage.get('location', 'Sverige')
        if "Driftstörning" in location:
             # Location already contains title text, use it as is
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

        from common.engine import classify_services
        
        # Build context for classification
        context_text = f"{location} {desc_sv} {title_sv}"
        affected_services = classify_services(context_text)
        
        # Filter out 'voice' and 'data' as requested by user
        affected_services = [s for s in affected_services if s not in [ServiceType.VOICE, ServiceType.MOBILE_DATA]]
        
        # Remove 'mobile' if we have more specific generations to keep it cleaner
        # (Optional, but usually better if we have 5G etc.)
        # However, user wants "mobile" specifically for Tre.

        inc_id = parsed_outage.get('id')
        
        from scrapers.common.translation import SWEDISH_COUNTIES
        from scrapers.common.engine import extract_region_from_text
        import requests, time
        
        # 1. Try local extraction first
        lookup_text = f"{location} {title_sv} {desc_sv}"
        county_name = extract_region_from_text(lookup_text, SWEDISH_COUNTIES)
        
        # 2. If it fails, try Nominatim reverse geocoding
        if not county_name and location.lower() not in ['sverige', 'hela sverige']:
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
                            county_name = extract_region_from_text(resolved_county, SWEDISH_COUNTIES) or resolved_county
                time.sleep(1) # respectful rate limit
            except:
                pass
                
        # 3. If STILL no county, the user demands ONLY Regions. We must drop it.
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
        logger.error(f"Error mapping Tre: {e}")
        return None

def map_tre_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    return [map_to_normalized(p) for p in parsed_outages if map_to_normalized(p)]
