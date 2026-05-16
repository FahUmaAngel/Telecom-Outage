"""
Enhanced Telia outage data parser.
Parses API responses from CoveragePortal and GLUP systems.
Supports bilingual output (Swedish-English).
"""
from typing import List, Dict, Optional, Any
import logging
import json
import sys
import os
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.translation import create_bilingual_text, SWEDISH_CITIES, SWEDISH_COUNTIES

logger = logging.getLogger(__name__)

# Constants to avoid duplication
MOBILE_NETWORK = 'Mobile Network'

def parse_mobile_outage(data: Dict) -> Optional[Dict]:
    """Parse mobile network outage from CoveragePortal API response."""
    try:
        outage = {}
        outage['id'] = data.get('FaultId') or data.get('ExternalId')
        
        text = data.get('Text', '')
        if text:
            outage['description'] = create_bilingual_text(text)
        
        if 'EventTime' in data:
            outage['start_time'] = data['EventTime']
        
        if 'EstimatedCloseTime' in data:
            outage['estimated_fix_time'] = data['EstimatedCloseTime']
        
        location = extract_location_from_text(text)
        if location:
            outage['location'] = location
        elif '_region_name' in data:
            outage['location'] = data['_region_name']
        
        outage['severity'] = determine_severity_from_text(text)
        outage['affected_services'] = extract_services_from_text(text)
        
        return outage if outage.get('id') or outage.get('description') else None
        
    except Exception as e:
        logger.error(f"Error parsing mobile outage: {e}")
        return None

def parse_fixed_outage(data: Dict) -> Optional[Dict]:
    """Parse fixed network outage from GLUP API response."""
    try:
        outage = {}
        if 'affected_counties' in data:
            counties_text = data['affected_counties']
            if counties_text and len(counties_text.strip()) > 0:
                outage['affected_counties'] = parse_counties_list(counties_text)
        
        if 'important_info' in data:
            info_text = data['important_info']
            if info_text and len(info_text.strip()) > 0:
                outage['description'] = create_bilingual_text(info_text)
        
        return outage if outage else None
    except Exception as e:
        logger.error(f"Error parsing fixed outage: {e}")
        return None

def extract_location_from_text(text: str) -> Optional[str]:
    """Extract location (city or county) from Swedish text."""
    if not text:
        return None
    
    # Check for counties first (more specific)
    for county in SWEDISH_COUNTIES:
        if county.lower() in text.lower():
            return county
    
    # Check for cities
    for city in SWEDISH_CITIES:
        if city.lower() in text.lower():
            return city
    
    # Look for location patterns
    location_patterns = [
        r'i\s+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)?)',
        r'vid\s+([A-ZÅÄÖ][a-zåäö]+)',
        r'område\s+([A-ZÅÄÖ][a-zåäö]+)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def determine_severity_from_text(text: str) -> str:
    """Determine severity level from Swedish text."""
    if not text:
        return "medium"
    
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ['kritisk', 'allvarlig', 'omfattande', 'stor störning', 'major']):
        return "critical"
    
    if any(kw in text_lower for kw in ['stor', 'betydande', 'viktig', 'omfattar']):
        return "high"
    
    if any(kw in text_lower for kw in ['liten', 'begränsad', 'lokal', 'minor']):
        return "low"
    
    return "medium"

def extract_services_from_text(text: str) -> List[str]:
    """Extract affected services from Swedish text."""
    if not text:
        return []
    
    services = []
    text_lower = text.lower()
    
    service_keywords = {
        'mobilnät': MOBILE_NETWORK,
        'mobil': MOBILE_NETWORK,
        '5g': '5G',
        '4g': '4G',
        'lte': 'LTE',
        '3g': '3G',
        '2g': '2G',
        'surf': 'Data',
        'data': 'Data',
        'samtal': 'Voice Calls',
        'telefoni': 'Telephony',
        'sms': 'SMS',
        'mms': 'MMS',
    }
    
    for keyword, service in service_keywords.items():
        if keyword in text_lower and service not in services:
            services.append(service)
    
    return services if services else [MOBILE_NETWORK]

def parse_counties_list(text: str) -> List[str]:
    """Parse list of affected counties from GLUP response."""
    return [county for county in SWEDISH_COUNTIES if county in text]

def _process_raw_entry(raw: Any) -> Optional[Dict]:
    """Process a single raw outage entry."""
    try:
        if hasattr(raw, 'raw_data'):
            data = raw.raw_data
            source_url = raw.source_url
        else:
            data = raw
            source_url = None
        
        if not isinstance(data, dict):
            return None

        outage = None
        if 'FaultId' in data or 'Text' in data:
            outage = parse_mobile_outage(data)
        elif 'affected_counties' in data or 'important_info' in data:
            outage = parse_fixed_outage(data)
        else:
            logger.warning(f"Unknown outage format: {list(data.keys())}")
            
        if outage and source_url:
            outage['source_url'] = source_url
            
        return outage
    except Exception as e:
        logger.error(f"Error processing raw entry: {e}")
        return None

def parse_telia_outages(raw_outages: List) -> List[Dict]:
    """Parse list of raw Telia outages."""
    parsed = []
    for raw in raw_outages:
        outage = _process_raw_entry(raw)
        if outage:
            parsed.append(outage)
    
    logger.info(f"Parsed {len(parsed)} outages from {len(raw_outages)} raw entries")
    return parsed
