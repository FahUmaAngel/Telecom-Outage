"""
Shared logic for Enghouse Networks Coverage Portals.
Used by Telia and Lycamobile (via Telenor).
"""
import requests
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from .models import RawOutage, OperatorEnum

logger = logging.getLogger(__name__)

class EnghouseFetcher:
    """Base fetcher for Enghouse Networks Coverage Portals."""
    
    def __init__(self, base_url: str, operator: OperatorEnum):
        self.base_url = base_url.rstrip('/')
        self.operator = operator
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self._token: Optional[str] = None

    def get_token(self) -> Optional[str]:
        """Extract session token (ert) from the portal."""
        try:
            # Usually the token is in the main page or in cookies/local storage logic
            # For Enghouse, it's often passed as a query param 'ert' or found in source
            url = f"{self.base_url}?appmode=outage"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Regex to find 'ert' assignment
                match = re.search(r'ert["\']?\s*[:=]\s*["\']([^"\']+)["\']', response.text)
                if match:
                    self._token = match.group(1)
                    return self._token
                
                # Check cookies
                if 'ert' in response.cookies:
                    self._token = response.cookies['ert']
                    return self._token
                    
            logger.warning(f"[{self.operator}] Could not extract session token")
            return None
            
        except Exception as e:
            logger.error(f"[{self.operator}] Error extracting token: {e}")
            return None

    def get_messages(self) -> List[RawOutage]:
        """Get important messages (usually doesn't require token)."""
        outages = []
        try:
            url = f"{self.base_url}/ImportantMessages/GetMessages"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                messages = response.json()
                if isinstance(messages, list):
                    for msg in messages:
                        outages.append(RawOutage(
                            operator=self.operator,
                            source_url=url,
                            raw_data=msg,
                            scraped_at=datetime.now()
                        ))
            else:
                logger.warning(f"[{self.operator}] Failed to get messages: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching messages: {e}")
            
        return outages

    def get_area_tickets(self, bbox: Dict[str, float], services: str) -> List[RawOutage]:
        """Get area tickets (outages) for a bounding box."""
        outages = []
        # Try to get token, but proceed even if it fails as some endpoints might work without it
        token = self._token or self.get_token()
        
        if not token:
            logger.warning(f"[{self.operator}] No token found, trying request without authentication")

        try:
            url = f"{self.base_url}/Fault/AreaTicketList"
            params = {
                **bbox,
                'services': services
            }
            if token:
                params['ert'] = token # Only add if we have it
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Handle cases where response might be empty or invalid JSON
                if not response.text.strip():
                     logger.warning(f"[{self.operator}] Empty response from AreaTicketList")
                     return outages

                try:
                    tickets = response.json()
                    if isinstance(tickets, list):
                        for ticket in tickets:
                            outages.append(RawOutage(
                                operator=self.operator,
                                source_url=url,
                                raw_data=ticket,
                                scraped_at=datetime.now()
                            ))
                except ValueError: # JSONDecodeError
                    logger.warning(f"[{self.operator}] Invalid JSON from AreaTicketList")
            else:
                logger.warning(f"[{self.operator}] Failed to get area tickets: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching area tickets: {e}")
            
        return outages
