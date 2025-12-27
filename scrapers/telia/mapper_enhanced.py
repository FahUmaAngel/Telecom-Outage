"""
Enhanced Telia mapper - converts parsed data to NormalizedOutage format.
Includes bilingual support and improved data mapping.
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
from common.translation import translate_swedish_to_english

logger = logging.getLogger(__name__)


def map_severity(severity_str: str) -> SeverityLevel:
    """Map severity string to SeverityLevel enum."""
    severity_map = {
        'critical': SeverityLevel.CRITICAL,
        'high': SeverityLevel.HIGH,
        'medium': SeverityLevel.MEDIUM,
        'low': SeverityLevel.LOW
    }
    return severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)


def map_services(services: List[str]) -> List[ServiceType]:
    """Map service strings to ServiceType enums."""
    service_map = {
        'mobile network': ServiceType.MOBILE,
        'mobilnät': ServiceType.MOBILE,
        'mobiltelefoni': ServiceType.MOBILE,
        '5g': ServiceType.MOBILE_5G,
        '4g': ServiceType.MOBILE_4G,
        'lte': ServiceType.MOBILE_4G,
        '3g': ServiceType.MOBILE_3G,
        '2g': ServiceType.MOBILE_2G,
        'data': ServiceType.MOBILE_DATA,
        'surf': ServiceType.MOBILE_DATA,
        'internet': ServiceType.MOBILE_DATA,
        'voice calls': ServiceType.VOICE,
        'telephony': ServiceType.VOICE,
        'samtal': ServiceType.VOICE,
        'röst': ServiceType.VOICE,
        'sms': ServiceType.SMS,
        'mms': ServiceType.MMS,
        'broadband': ServiceType.BROADBAND,
        'bredband': ServiceType.BROADBAND,
        'fiber': ServiceType.FIBER,
        'tv': ServiceType.TV,
    }
    
    mapped = []
    for service in services:
        service_lower = service.lower()
        # Simple substring match for robustness
        for key, value in service_map.items():
            if key in service_lower:
                if value not in mapped:
                    mapped.append(value)
    
    return mapped if mapped else [ServiceType.MOBILE]


def determine_status(parsed_outage: Dict) -> OutageStatus:
    """Determine outage status from parsed data."""
    # Check if there's an estimated fix time
    if parsed_outage.get('estimated_fix_time'):
        return OutageStatus.ACTIVE
    
    # Check description for status keywords
    desc = parsed_outage.get('description', {})
    if isinstance(desc, dict):
        text = desc.get('sv', '') + ' ' + desc.get('en', '')
    else:
        text = str(desc)
    
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ['löst', 'resolved', 'åtgärdat']):
        return OutageStatus.RESOLVED
    elif any(kw in text_lower for kw in ['undersöker', 'investigating', 'analyserar']):
        return OutageStatus.INVESTIGATING
    elif any(kw in text_lower for kw in ['planerad', 'scheduled', 'planerat']):
        return OutageStatus.SCHEDULED
    
    return OutageStatus.ACTIVE


def create_bilingual_description(parsed_outage: Dict) -> Dict[str, str]:
    """Create bilingual description from parsed outage."""
    desc = parsed_outage.get('description', {})
    
    if isinstance(desc, dict) and 'sv' in desc and 'en' in desc:
        return desc
    
    # If only Swedish text is available
    if isinstance(desc, str):
        return {
            'sv': desc,
            'en': translate_swedish_to_english(desc)
        }
    
    return {'sv': '', 'en': ''}


def map_to_normalized_outage(parsed_outage: Dict) -> Optional[NormalizedOutage]:
    """
    Map parsed outage to NormalizedOutage model.
    
    Args:
        parsed_outage: Parsed outage dictionary from parser
        
    Returns:
        NormalizedOutage object or None
    """
    try:
        # Create bilingual description
        description = create_bilingual_description(parsed_outage)
        
        # Parse timestamps
        start_time = None
        if 'start_time' in parsed_outage:
            try:
                start_time = datetime.fromisoformat(parsed_outage['start_time'].replace('Z', '+00:00'))
            except:
                pass
        
        estimated_fix_time = None
        if 'estimated_fix_time' in parsed_outage:
            try:
                estimated_fix_time = datetime.fromisoformat(parsed_outage['estimated_fix_time'].replace('Z', '+00:00'))
            except:
                pass
        
        # Create NormalizedOutage
        outage = NormalizedOutage(
            operator=OperatorEnum.TELIA,
            outage_id=parsed_outage.get('id', f"telia_{datetime.now().timestamp()}"),
            title={
                'sv': f"Störning i {parsed_outage.get('location', 'Sverige')}",
                'en': f"Outage in {parsed_outage.get('location', 'Sweden')}"
            },
            description=description,
            severity=map_severity(parsed_outage.get('severity', 'medium')),
            status=determine_status(parsed_outage),
            affected_services=map_services(parsed_outage.get('affected_services', [])),
            location=parsed_outage.get('location'),
            start_time=start_time or datetime.now(),
            estimated_fix_time=estimated_fix_time,
            source_url=parsed_outage.get('source_url')
        )
        
        return outage
        
    except Exception as e:
        logger.error(f"Error mapping outage to normalized format: {e}")
        return None


def map_telia_outages(parsed_outages: List[Dict]) -> List[NormalizedOutage]:
    """
    Map list of parsed outages to NormalizedOutage objects.
    
    Args:
        parsed_outages: List of parsed outage dictionaries
        
    Returns:
        List of NormalizedOutage objects
    """
    normalized = []
    
    for parsed in parsed_outages:
        outage = map_to_normalized_outage(parsed)
        if outage:
            normalized.append(outage)
    
    logger.info(f"Mapped {len(normalized)} outages to normalized format")
    return normalized


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample parsed outage
    sample_parsed = {
        "id": "12345",
        "description": {
            "sv": "På grund av ett kabelfel i Stockholm kan du uppleva störningar i mobilnätet.",
            "en": "Due to a cable fault in Stockholm you may experience disruptions in the mobile network."
        },
        "start_time": "2025-12-26T10:00:00",
        "estimated_fix_time": "2025-12-26T18:00:00",
        "location": "Stockholm",
        "severity": "medium",
        "affected_services": ["Mobile Network", "4G"]
    }
    
    print("Testing mapper:")
    result = map_to_normalized_outage(sample_parsed)
    if result:
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False, default=str))
