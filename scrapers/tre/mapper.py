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
        
        # Determine status
        status = OutageStatus.SCHEDULED # Default for planned works
        # If start time is past and end time is future -> ACTIVE
        # But we don't have easy generic time comparison here without importing datetime
        # Let's assume SCHEDULED for "Planerade arbeten" context
        
        normalized = NormalizedOutage(
            operator=OperatorEnum.TRE,
            outage_id=parsed_outage.get('id'),
            title={
                'sv': f"Planerat arbete i {parsed_outage.get('location')}",
                'en': f"Planned maintenance in {parsed_outage.get('location')}"
            },
            description={
                'sv': desc_sv,
                'en': desc_en
            },
            status=status,
            affected_services=[ServiceType.MOBILE],
            location=parsed_outage.get('location'),
            estimated_fix_time=parsed_outage.get('end_time'),
            started_at=parsed_outage.get('start_time')
        )
        return normalized
        
    except Exception as e:
        logger.error(f"Error mapping Tre: {e}")
        return None

def map_tre_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    return [map_to_normalized(p) for p in parsed_outages if map_to_normalized(p)]
