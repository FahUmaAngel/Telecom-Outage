"""
Core Engine Services: Severity Scoring and Analytics tools.
"""
from typing import List
from .models import OutageStatus, SeverityLevel, ServiceType

from datetime import datetime, timedelta
import re

def parse_swedish_date(date_str: str) -> datetime:
    """
    Parse Swedish date strings into datetime objects.
    Supported formats:
    - 'ons 18.feb 14:55' (Telia)
    - '2026-02-15 Kl 00:00' (Tre)
    """
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    
    # Tre Format: 2026-02-15 Kl 00:00
    if 'kl' in date_str:
        try:
            clean = date_str.replace('kl', '').replace('  ', ' ').strip()
            return datetime.strptime(clean, "%Y-%m-%d %H:%M")
        except:
            pass

    # Telia/Lyca Format: 'ons 18.feb 14:55'
    # Month mapping
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'maj': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
    }
    
    try:
        # Match '18.feb 14:55' or similar
        match = re.search(r'(\d{1,2})[\.\s]([a-z]{3})\s+(\d{1,2}:\d{2})', date_str)
        if match:
            day = int(match.group(1))
            month_abbr = match.group(2)
            time_part = match.group(3)
            month = months.get(month_abbr)
            
            if month:
                # Use current year as default
                now = datetime.now()
                year = now.year
                
                # Logic to handle year rollover: 
                # if we are in Jan/Feb and see dates from Nov/Dec, 
                # and no year was specified, it's likely previous year.
                # Specifically: if the parsed date is > 1 month in the future, it's likely last year.
                test_dt = datetime(year, month, day)
                if test_dt > now + timedelta(days=30):
                    year -= 1
                
                dt_str = f"{year}-{month:02d}-{day:02d} {time_part}"
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except:
        pass

    # Basic ISO format fallback
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        pass
        
    return None

def calculate_severity_score(severity: SeverityLevel, affected_services: List[ServiceType]) -> float:
    """
    Calculate a normalized severity score (0.0 to 10.0).
    Factors:
    - Base severity (Critical=1.0, High=0.8, Medium=0.5, Low=0.2)
    - Service impact (5G/4G weight higher)
    """
    severity_weights = {
        SeverityLevel.CRITICAL: 1.0,
        SeverityLevel.HIGH: 0.8,
        SeverityLevel.MEDIUM: 0.5,
        SeverityLevel.LOW: 0.2
    }
    
    base_weight = severity_weights.get(severity, 0.5)
    
    # Multiplier based on generation (newer = higher impact)
    service_multiplier = 1.0
    high_impact = [ServiceType.MOBILE_5G_PLUS, ServiceType.MOBILE_5G, ServiceType.MOBILE_4G]
    
    for service in affected_services:
        if service in high_impact:
            service_multiplier += 0.5
        else:
            service_multiplier += 0.2
            
    score = (base_weight * service_multiplier) * 5.0
    return min(10.0, score)

def extract_region_from_text(text: str, counties: List[str]) -> str:
    """
    Extract a region (county) from a text string.
    Uses direct matching, base name matching (handling possessive 's'), and city-to-county mapping.
    """
    if not text:
        return None
        
    text_lower = text.lower()
    
    # 1. Check for direct county matches (e.g. "Stockholms län")
    for county in counties:
        # Check exact lower match first
        if county.lower() in text_lower:
            return county
            
        base_name = county.replace(" län", "").lower()
        # Handle Swedish possessive 's' (e.g., "Västernorrlands" vs "Västernorrland")
        base_name_no_s = base_name.rstrip('s')
        
        # Match if the base name (with or without 's') is in the text
        if base_name in text_lower or base_name_no_s in text_lower:
            return county
            
    # 2. Check for city matches using CITY_TO_COUNTY mapping
    from scrapers.common.translation import CITY_TO_COUNTY
    for city, county in CITY_TO_COUNTY.items():
        if city.lower() in text_lower:
            return county
            
    return None


def classify_services(text: str) -> List[ServiceType]:
    """
    Extract mobile generation ServiceTypes from text.
    Only returns: 5G+, 5G, 4G, 3G, 2G.
    """
    if not text:
        return [ServiceType.MOBILE_4G, ServiceType.MOBILE_5G]

    services = set()
    text_lower = text.lower()

    # Detect mobile generations (order matters: 5G+ before 5G)
    if any(k in text_lower for k in ['5g+', '5g plus', '5g-plus']):
        services.add(ServiceType.MOBILE_5G_PLUS)

    if '5g' in text_lower and ServiceType.MOBILE_5G_PLUS not in services:
        services.add(ServiceType.MOBILE_5G)

    if '4g' in text_lower:
        services.add(ServiceType.MOBILE_4G)

    if '3g' in text_lower:
        services.add(ServiceType.MOBILE_3G)

    if '2g' in text_lower:
        services.add(ServiceType.MOBILE_2G)

    # Fallback: if nothing detected, assume 4G and 5G (modern standard)
    if not services:
        return [ServiceType.MOBILE_4G, ServiceType.MOBILE_5G]

    return sorted(services)


def classify_status(text: str, current_status: OutageStatus = OutageStatus.ACTIVE) -> OutageStatus:
    """
    Determine OutageStatus based on text context.
    """
    if not text:
        return current_status

    text_lower = text.lower()

    if any(k in text_lower for k in ['löst', 'resolved', 'åtgärdat', 'klart']):
        return OutageStatus.RESOLVED
    if any(k in text_lower for k in ['planerat', 'scheduled', 'kommande', 'underhåll']):
        return OutageStatus.SCHEDULED
    if any(k in text_lower for k in ['undersöker', 'investigating', 'felsökning', 'pågår']):
        return OutageStatus.INVESTIGATING

    return current_status
