import re
from datetime import datetime, timezone
from typing import List, Optional
import hashlib

def extract_datetime(text: str) -> Optional[datetime]:
    """
    Extracts datetime from Tele2 Swedish text like:
    'kl. 16:00 den 20 mars' or 'kl 10:00 21/03'
    """
    if not text:
        return None
        
    # Example: 16:00 den 20 mars
    months = {
        'januari': 1, 'februari': 2, 'mars': 3, 'april': 4, 'maj': 5, 'juni': 6,
        'juli': 7, 'augusti': 8, 'september': 9, 'oktober': 10, 'november': 11, 'december': 12
    }
    
    # Try 'kl. HH:MM den DD månad'
    match = re.search(r'kl\.?\s*(\d{1,2}):(\d{2})\s+den\s+(\d{1,2})\s+([a-zåäö]+)', text.lower())
    if match:
        hh, mm, dd, month_str = match.groups()
        month = months.get(month_str, datetime.now().month)
        year = datetime.now().year
        try:
            return datetime(year, month, int(dd), int(hh), int(mm), tzinfo=timezone.utc)
        except ValueError:
            return None
            
    # Try 'DD/MM kl HH:MM'
    match = re.search(r'(\d{1,2})/(\d{1,2})\s+kl\.?\s*(\d{1,2}):(\d{2})', text)
    if match:
        dd, mm, hh, min_ = match.groups()
        year = datetime.now().year
        try:
            return datetime(year, int(mm), int(dd), int(hh), int(min_), tzinfo=timezone.utc)
        except ValueError:
            return None
            
    return None

def map_tele2_to_outage(address_info: dict, status_text: str, detailed_text: str = ""):
    """
    Maps a Tele2 address probe result to a standard Outage record.
    address_info: {"city": "Stockholm", "address": "...", "lat": ..., "lng": ...}
    status_text: Header text (e.g. "Driftstörning")
    detailed_text: Description text with dates
    """
    is_outage = "störning" in status_text.lower() or "avbrott" in status_text.lower() or "fel" in status_text.lower()
    
    if not is_outage:
        return None
        
    now = datetime.now(timezone.utc)
    
    # Generate a deterministic ID based on address and date
    # Tele2 doesn't give a public ID for these, so we make one
    addr_hash = hashlib.sha256(address_info['address'].encode()).hexdigest()[:6].upper()
    incident_id = f"TELE2-{addr_hash}-{now.strftime('%y%m%d')}"
    
    # Extract estimated end time
    end_time = extract_datetime(detailed_text)
    
    return {
        "incident_id": incident_id,
        "operator": "Tele2",
        "status": "active",
        "severity": "medium",
        "title": f"Driftstörning i {address_info['city']}",
        "description": detailed_text or status_text,
        "location": f"{address_info['address']}, {address_info['city']}",
        "latitude": address_info.get('lat'),
        "longitude": address_info.get('lng'),
        "affected_services": "4g, 5g", # Tele2 mobile is primarily 4G/5G for drift maps
        "start_time": now.isoformat(),
        "end_time": end_time.isoformat() if end_time else None
    }
