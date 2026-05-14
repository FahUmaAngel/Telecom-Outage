import re
from datetime import datetime, timezone
from typing import List, Optional
import hashlib
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel, ServiceType
from scrapers.common.engine import classify_status, classify_services

def extract_datetime(text: str) -> Optional[datetime]:
    """
    Extracts datetime from Tele2 Swedish text.
    """
    if not text:
        return None
        
    months = {
        'januari': 1, 'februari': 2, 'mars': 3, 'april': 4, 'maj': 5, 'juni': 6,
        'juli': 7, 'augusti': 8, 'september': 9, 'oktober': 10, 'november': 11, 'december': 12
    }
    
    match = re.search(r'kl\.?\s*(\d{1,2}):(\d{2})\s+den\s+(\d{1,2})\s+([a-zåäö]+)', text.lower())
    if match:
        hh, mm, dd, month_str = match.groups()
        month = months.get(month_str, datetime.now().month)
        year = datetime.now().year
        try:
            return datetime(year, month, int(dd), int(hh), int(mm), tzinfo=timezone.utc)
        except ValueError:
            return None
            
    match = re.search(r'(\d{1,2})/(\d{1,2})\s+kl\.?\s*(\d{1,2}):(\d{2})', text)
    if match:
        dd, mm, hh, min_ = match.groups()
        year = datetime.now().year
        try:
            return datetime(year, int(mm), int(dd), int(hh), int(min_), tzinfo=timezone.utc)
        except ValueError:
            return None
            
    return None

def map_tele2_to_outage(address_info: dict, status_text: str, detailed_text: str = "") -> Optional[NormalizedOutage]:
    """
    Maps a Tele2 address probe result to a NormalizedOutage.
    """
    context = f"{status_text} {detailed_text}"
    status = classify_status(context, OutageStatus.ACTIVE)
    
    # If explicitly scheduled/planned, we might skip it later, but let's map it first
    if status == OutageStatus.SCHEDULED:
        # In current requirement, we don't even want to store these.
        return None

    now = datetime.now(timezone.utc)
    
    addr_hash = hashlib.sha256(address_info['address'].encode()).hexdigest()[:6].upper()
    incident_id = f"TELE2-{addr_hash}-{now.strftime('%y%m%d')}"
    
    end_time = extract_datetime(detailed_text)
    
    normalized = NormalizedOutage(
        operator=OperatorEnum.TELE2,
        incident_id=incident_id,
        title={"sv": f"Driftstörning i {address_info['city']}", "en": f"Service disruption in {address_info['city']}"},
        description={"sv": detailed_text or status_text, "en": detailed_text or status_text}, # Simple copy for now
        location=address_info['city'],
        status=status,
        severity=SeverityLevel.MEDIUM,
        affected_services=classify_services(context),
        started_at=now,
        end_time=end_time if status == OutageStatus.RESOLVED else None,
        source_url="https://www.tele2.se/driftstorning-mobilnatet"
    )
    
    return normalized
