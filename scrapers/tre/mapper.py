"""
Tre mapper.
"""
from typing import List, Dict, Optional
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import (
    NormalizedOutage,
    OperatorEnum,
    SeverityLevel,
    OutageStatus,
    ServiceType
)
from common.translation import translate_swedish_to_english

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

        # Map services
        raw_services = parsed_outage.get('affected_services', [])
        affected_services = []
        
        service_map = {
            '5G': ServiceType.MOBILE_5G,
            '4G': ServiceType.MOBILE_4G,
            '3G': ServiceType.MOBILE_3G,
            '2G': ServiceType.MOBILE_2G,
            'Mobile Data': ServiceType.MOBILE_DATA,
            'Voice': ServiceType.VOICE,
            'SMS': ServiceType.SMS,
            'Mobile Network': ServiceType.MOBILE
        }
        
        for s in raw_services:
            if s in service_map:
                affected_services.append(service_map[s])
        
        if not affected_services:
            affected_services = [ServiceType.MOBILE]

        normalized = NormalizedOutage(
            operator=OperatorEnum.TRE,
            outage_id=parsed_outage.get('id'),
            title={
                'sv': title_sv,
                'en': title_en
            },
            description={
                'sv': desc_sv,
                'en': desc_en
            },
            status=status,
            affected_services=affected_services,
            location=parsed_outage.get('location'),
            estimated_fix_time=parsed_outage.get('end_time'),
            # Use started_at for start_time
            start_time=parsed_outage.get('start_time')
        )
        return normalized
        
    except Exception as e:
        logger.error(f"Error mapping Tre: {e}")
        return None

def map_tre_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    return [map_to_normalized(p) for p in parsed_outages if map_to_normalized(p)]
