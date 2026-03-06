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
    - Service impact (Mobile/Internet weight 1.5, Landline 1.0)
    """
    severity_weights = {
        SeverityLevel.CRITICAL: 1.0,
        SeverityLevel.HIGH: 0.8,
        SeverityLevel.MEDIUM: 0.5,
        SeverityLevel.LOW: 0.2
    }
    
    base_weight = severity_weights.get(severity, 0.5)
    
    # Simple multiplier based on service types
    service_multiplier = 1.0
    critical_services = [ServiceType.MOBILE, ServiceType.INTERNET, ServiceType.VOIP]
    
    for service in affected_services:
        if service in critical_services:
            service_multiplier += 0.5
        else:
            service_multiplier += 0.2
            
    # Max out at 10.0
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
    Extract ServiceType enums from text based on keywords.
    """
    if not text:
        return [ServiceType.MOBILE]

    services = []
    text_lower = text.lower()

    # Specific mobile generations (Order matters for 5G+ vs 5G)
    if '5g+' in text_lower or '5g plus' in text_lower: services.append(ServiceType.MOBILE_5G_PLUS)
    if '5g' in text_lower and ServiceType.MOBILE_5G_PLUS not in services: 
        services.append(ServiceType.MOBILE_5G)
    
    if '4g' in text_lower or 'lte' in text_lower: services.append(ServiceType.MOBILE_4G)
    if '3g' in text_lower or 'umts' in text_lower: services.append(ServiceType.MOBILE_3G)
    if '2g' in text_lower or 'gsm' in text_lower: services.append(ServiceType.MOBILE_2G)

    # General categories
    if any(k in text_lower for k in ['data', 'surf', 'internet', 'mobilsurf', 'browsing', 'low speed']):
        services.append(ServiceType.MOBILE_DATA)
    if any(k in text_lower for k in ['samtal', 'röst', 'voice', 'telefoni', 'mobilsamtal', 'calling']):
        services.append(ServiceType.VOICE)
    if 'sms' in text_lower or 'text message' in text_lower: services.append(ServiceType.SMS)
    if 'mms' in text_lower: services.append(ServiceType.MMS)

    # Non-mobile
    if 'fiber' in text_lower or 'stadsnät' in text_lower: services.append(ServiceType.FIBER)
    if any(k in text_lower for k in ['bredband', 'broadband', 'fixed line', 'adsl', 'vDSL']):
        services.append(ServiceType.BROADBAND)

    # If it mentions generic mobile terms and no specific generation is found
    if not any(s in [ServiceType.MOBILE_5G_PLUS, ServiceType.MOBILE_5G, ServiceType.MOBILE_4G, ServiceType.MOBILE_3G, ServiceType.MOBILE_2G, ServiceType.VOICE, ServiceType.MOBILE_DATA] for s in services):
        mobile_keywords = ['täckning', 'mobil', 'nätverk', 'network', 'driftstörning', 'underhåll', 'arbete', 'coverage', 'störning']
        if any(k in text_lower for k in mobile_keywords):
             # If it's a mobile-related general term, add the core standard modern generations
             # 5G+ is ONLY added if explicitly detected in the first pass
             if 'fiber' not in text_lower and 'bredband' not in text_lower:
                services.extend([
                    ServiceType.MOBILE_5G, 
                    ServiceType.MOBILE_4G, 
                    ServiceType.VOICE, 
                    ServiceType.MOBILE_DATA
                ])

    # If the list is empty or only contains generic 'mobile', expand it
    # Note: We NO LONGER add 5G+ as a default fallback to avoid inaccuracy
    if not services or (len(services) == 1 and services[0] == ServiceType.MOBILE):
        if 'fiber' not in text_lower and 'bredband' not in text_lower:
            return [
                ServiceType.MOBILE_5G, 
                ServiceType.MOBILE_4G, 
                ServiceType.VOICE, 
                ServiceType.MOBILE_DATA
            ]
        elif not services:
            return [ServiceType.MOBILE]

    # Filter out the generic 'mobile' if we have specific generations
    if len(services) > 1 and ServiceType.MOBILE in services:
        services.remove(ServiceType.MOBILE)

    return list(set(services))


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
