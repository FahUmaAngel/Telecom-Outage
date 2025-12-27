"""
Lycamobile mapper.
"""
from typing import List, Dict, Optional
from datetime import datetime
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

logger = logging.getLogger(__name__)

def map_to_normalized(parsed_outage: Dict) -> Optional[NormalizedOutage]:
    try:
        outage = NormalizedOutage(
            operator=OperatorEnum.LYCAMOBILE,
            outage_id=parsed_outage.get('id'),
            title={
                'sv': f"Störning i {parsed_outage.get('location', 'Sverige')}",
                'en': f"Outage in {parsed_outage.get('location', 'Sweden')}"
            },
            description=parsed_outage.get('description'),
            status=OutageStatus.ACTIVE, # Default to active for now
            affected_services=[ServiceType.MOBILE],
            location=parsed_outage.get('location'),
            # Parsing dates... simplified for now, should use proper ISO parsing
            # started_at=...
        )
        return outage
    except Exception as e:
        logger.error(f"Error mapping Lyca: {e}")
        return None

def map_lyca_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    return [map_to_normalized(p) for p in parsed_outages if map_to_normalized(p)]
