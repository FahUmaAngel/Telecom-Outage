"""
Enhanced Telia outage data parser.
Parses API responses from CoveragePortal and GLUP systems.
Supports bilingual output (Swedish-English).
"""
from typing import List, Dict, Optional
import logging
import json
import sys
import os
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.translation import create_bilingual_text, SWEDISH_CITIES, SWEDISH_COUNTIES

logger = logging.getLogger(__name__)


def parse_mobile_outage(data: Dict) -> Optional[Dict]:
    """
    Parse mobile network outage from CoveragePortal API response.
    
    Expected format:
    {
        "FaultId": "12345",
        "Text": "På grund av ett kabelfel...",
        "EventTime": "2025-12-26T10:00:00",
        "EstimatedCloseTime": "2025-12-26T18:00:00",
        "ExternalId": "EXT-123"
    }
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Parsed outage dictionary or None
    """
    try:
        outage = {}
        
        # Extract ID
        outage['id'] = data.get('FaultId') or data.get('ExternalId')
        
        # Extract and translate description
        text = data.get('Text', '')
        if text:
            outage['description'] = create_bilingual_text(text)
        
        # Extract timestamps
        if 'EventTime' in data:
            outage['start_time'] = data['EventTime']
        
        if 'EstimatedCloseTime' in data:
            outage['estimated_fix_time'] = data['EstimatedCloseTime']
        
        # Extract location if mentioned in text
        location = extract_location_from_text(text)
        if location:
            outage['location'] = location
        
        # Determine severity from text
        outage['severity'] = determine_severity_from_text(text)
        
        # Extract affected services
        outage['affected_services'] = extract_services_from_text(text)
        
        return outage if outage.get('id') or outage.get('description') else None
        
    except Exception as e:
        logger.error(f"Error parsing mobile outage: {e}")
        return None


def parse_fixed_outage(data: Dict) -> Optional[Dict]:
    """
    Parse fixed network outage from GLUP API response.
    
    Args:
        data: Raw API response dictionary
        
    Returns:
        Parsed outage dictionary or None
    """
    try:
        outage = {}
        
        # GLUP format varies - handle different structures
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
        r'i\s+([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)?)',  # "i Stockholm"
        r'vid\s+([A-ZÅÄÖ][a-zåäö]+)',  # "vid Uppsala"
        r'område\s+([A-ZÅÄÖ][a-zåäö]+)',  # "område Malmö"
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
    
    # Critical keywords
    critical_keywords = ['kritisk', 'allvarlig', 'omfattande', 'stor störning', 'major']
    if any(kw in text_lower for kw in critical_keywords):
        return "critical"
    
    # High severity
    high_keywords = ['stor', 'betydande', 'viktig', 'omfattar']
    if any(kw in text_lower for kw in high_keywords):
        return "high"
    
    # Low severity
    low_keywords = ['liten', 'begränsad', 'lokal', 'minor']
    if any(kw in text_lower for kw in low_keywords):
        return "low"
    
    return "medium"


def extract_services_from_text(text: str) -> List[str]:
    """Extract affected services from Swedish text."""
    if not text:
        return []
    
    services = []
    text_lower = text.lower()
    
    service_keywords = {
        'mobilnät': 'Mobile Network',
        'mobil': 'Mobile Network',
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
    
    return services if services else ['Mobile Network']


def parse_counties_list(text: str) -> List[str]:
    """Parse list of affected counties from GLUP response."""
    counties = []
    
    # Try to extract county names
    for county in SWEDISH_COUNTIES:
        if county in text:
            counties.append(county)
    
    return counties


def parse_telia_outages(raw_outages: List) -> List[Dict]:
    """
    Parse list of raw Telia outages (from RawOutage.raw_data).
    
    Args:
        raw_outages: List of RawOutage objects or raw data dicts
        
    Returns:
        List of parsed outage dictionaries
    """
    parsed = []
    
    for raw in raw_outages:
        try:
            # Handle RawOutage objects
            if hasattr(raw, 'raw_data'):
                data = raw.raw_data
                source_url = raw.source_url
            else:
                data = raw
                source_url = None
            
            # Determine type and parse accordingly
            if isinstance(data, dict):
                # Check if it's mobile or fixed format
                if 'FaultId' in data or 'Text' in data:
                    # Mobile outage
                    outage = parse_mobile_outage(data)
                elif 'affected_counties' in data or 'important_info' in data:
                    # Fixed outage
                    outage = parse_fixed_outage(data)
                else:
                    logger.warning(f"Unknown outage format: {list(data.keys())}")
                    continue
                
                if outage:
                    if source_url:
                        outage['source_url'] = source_url
                    parsed.append(outage)
                    
        except Exception as e:
            logger.error(f"Error parsing outage: {e}")
            continue
    
    logger.info(f"Parsed {len(parsed)} outages from {len(raw_outages)} raw entries")
    return parsed


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample mobile outage
    sample_mobile = {
        "FaultId": "12345",
        "Text": "På grund av ett kabelfel i Stockholm kan du uppleva störningar i mobilnätet. Vi arbetar med att åtgärda felet.",
        "EventTime": "2025-12-26T10:00:00",
        "EstimatedCloseTime": "2025-12-26T18:00:00"
    }
    
    print("Testing mobile outage parser:")
    result = parse_mobile_outage(sample_mobile)
    print(json.dumps(result, indent=2, ensure_ascii=False))
