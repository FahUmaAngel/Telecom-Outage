"""
Lycamobile outage parser.
Similar to Telia parser but adapted if necessary.
"""
from typing import List, Dict, Optional
import logging
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.translation import create_bilingual_text, SWEDISH_CITIES, SWEDISH_COUNTIES

logger = logging.getLogger(__name__)

def parse_lyca_outage(data: Dict) -> Optional[Dict]:
    """
    Parse Lycamobile/Telenor outage.
    
    Format is likely identical to Telia (Enghouse standard).
    {
        "FaultId": "...",
        "Text": "...",
        "EventTime": "...",
        "EstimatedCloseTime": "..."
    }
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
            
        # Extract location if mentioned
        # Telenor data might not have explicit location field, parse text
        # (Same logic as Telia)
        location = _extract_location(text)
        if location:
            outage['location'] = location
            
        return outage if outage.get('id') else None
        
    except Exception as e:
        logger.error(f"Error parsing Lyca outage: {e}")
        return None

def _extract_location(text: str) -> Optional[str]:
    # Try to find county or city
    if not text: return None
    for county in SWEDISH_COUNTIES:
        if county.lower() in text.lower(): return county
    for city in SWEDISH_CITIES:
        if city.lower() in text.lower(): return city
    return "Sweden"

def parse_lyca_outages(raw_outages: List) -> List[Dict]:
    parsed = []
    for raw in raw_outages:
        try:
            data = raw.raw_data if hasattr(raw, 'raw_data') else raw
            outage = parse_lyca_outage(data)
            if outage:
                if hasattr(raw, 'source_url'):
                    outage['source_url'] = raw.source_url
                parsed.append(outage)
        except Exception:
            continue
    return parsed
