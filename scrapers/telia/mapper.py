"""
Telia data mapper.
Maps Telia-specific data format to standardized schema.
"""
from datetime import datetime
from typing import List, Dict, Optional
import logging
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import (
    NormalizedOutage,
    OperatorEnum,
    OutageStatus,
    SeverityLevel
)

logger = logging.getLogger(__name__)


def map_to_standard(raw_outages: List[Dict]) -> List[NormalizedOutage]:
    """
    Map Telia raw outage data to standardized format.
    
    Args:
        raw_outages: List of raw outage dictionaries from parser
        
    Returns:
        List of NormalizedOutage objects
    """
    normalized = []
    
    for raw in raw_outages:
        try:
            outage = map_single_outage(raw)
            if outage:
                normalized.append(outage)
        except Exception as e:
            logger.error(f"Error mapping outage: {e}")
            continue
    
    logger.info(f"Mapped {len(normalized)} Telia outages to standard format")
    return normalized


def map_single_outage(raw: Dict) -> Optional[NormalizedOutage]:
    """
    Map a single Telia outage to standardized format.
    
    Args:
        raw: Raw outage dictionary
        
    Returns:
        NormalizedOutage object or None
    """
    try:
        # Extract title
        title = raw.get('title') or raw.get('text_content', 'Unknown outage')
        if len(title) > 200:
            title = title[:200] + "..."
        
        # Extract description
        description = raw.get('description') or raw.get('text_content')
        
        # Extract location
        location = extract_location(raw)
        
        # Determine status
        status = determine_status(raw)
        
        # Determine severity
        severity = determine_severity(raw)
        
        # Extract affected services
        affected_services = extract_services(raw)
        
        # Create normalized outage
        outage = NormalizedOutage(
            operator=OperatorEnum.TELIA,
            incident_id=raw.get('id'),
            title=title,
            description=description,
            location=location,
            status=status,
            severity=severity,
            affected_services=affected_services
        )
        
        return outage
        
    except Exception as e:
        logger.error(f"Error in map_single_outage: {e}")
        return None


def extract_location(raw: Dict) -> Optional[str]:
    """Extract location from raw data."""
    location = raw.get('location')
    if location:
        return location
    
    # Try to extract from text content
    text = raw.get('text_content', '') + ' ' + raw.get('description', '')
    
    # Look for Swedish city/region names
    swedish_cities = [
        'Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås',
        'Örebro', 'Linköping', 'Helsingborg', 'Jönköping', 'Norrköping',
        'Lund', 'Umeå', 'Gävle', 'Borås', 'Södertälje'
    ]
    
    for city in swedish_cities:
        if city.lower() in text.lower():
            return city
    
    # Look for region patterns
    region_match = re.search(r'(i|vid|område|region)\s+([A-ZÅÄÖ][a-zåäö]+)', text)
    if region_match:
        return region_match.group(2)
    
    return None


def determine_status(raw: Dict) -> OutageStatus:
    """Determine outage status from raw data."""
    status_text = (
        raw.get('status', '') + ' ' + 
        raw.get('text_content', '')
    ).lower()
    
    if any(word in status_text for word in ['löst', 'resolved', 'åtgärdad', 'fixed']):
        return OutageStatus.RESOLVED
    elif any(word in status_text for word in ['planerad', 'scheduled', 'underhåll']):
        return OutageStatus.SCHEDULED
    elif any(word in status_text for word in ['undersök', 'investigating', 'utred']):
        return OutageStatus.INVESTIGATING
    else:
        return OutageStatus.ACTIVE


def determine_severity(raw: Dict) -> SeverityLevel:
    """Determine severity level from raw data."""
    text = (
        raw.get('title', '') + ' ' +
        raw.get('description', '') + ' ' +
        raw.get('text_content', '')
    ).lower()
    
    # Critical keywords
    if any(word in text for word in ['kritisk', 'critical', 'omfattande', 'major', 'allvarlig']):
        return SeverityLevel.CRITICAL
    
    # High severity keywords
    elif any(word in text for word in ['stor', 'high', 'betydande', 'viktig']):
        return SeverityLevel.HIGH
    
    # Low severity keywords
    elif any(word in text for word in ['liten', 'minor', 'begränsad', 'lokal']):
        return SeverityLevel.LOW
    
    # Default to medium
    return SeverityLevel.MEDIUM


def extract_services(raw: Dict) -> List[str]:
    """Extract affected services from raw data."""
    services = []
    text = (
        raw.get('title', '') + ' ' +
        raw.get('description', '') + ' ' +
        raw.get('text_content', '')
    ).lower()
    
    service_keywords = {
        'mobil': 'Mobile Network',
        'bredband': 'Broadband',
        'telefoni': 'Telephony',
        '4g': '4G',
        '5g': '5G',
        'fiber': 'Fiber',
        'internet': 'Internet',
        'tv': 'TV'
    }
    
    for keyword, service in service_keywords.items():
        if keyword in text:
            services.append(service)
    
    return services if services else ['Unknown']


if __name__ == "__main__":
    # Test the mapper
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    sample_raw = {
        'title': 'Störning i mobilnätet',
        'description': 'Omfattande störning i 4G-nätet i Stockholm området',
        'status': 'Aktiv',
        'location': 'Stockholm'
    }
    
    outage = map_single_outage(sample_raw)
    if outage:
        print("✓ Successfully mapped outage:")
        print(outage.model_dump_json(indent=2))
    else:
        print("✗ Failed to map outage")
