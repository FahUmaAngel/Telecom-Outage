import requests
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from urllib.parse import unquote
from .models import RawOutage, OperatorEnum

logger = logging.getLogger(__name__)

class EnghouseFetcher:
    """Base fetcher for Enghouse Networks Coverage Portals."""
    
    def __init__(self, base_url: str, operator: OperatorEnum, token_param: str = 'ert'):
        self.base_url = base_url.rstrip('/')
        self.operator = operator
        self.token_param = token_param
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self._token: Optional[str] = None

    def _extract_from_input(self, html: str) -> Optional[str]:
        """Check for <input id="csrft" value="...">"""
        match = re.search(r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', html)
        if not match:
            match = re.search(r'value=["\']([^"\']+)["\']\s+id=["\']csrft["\']', html)
        
        if match:
            token = unquote(match.group(1))
            logger.info(f"[{self.operator}] Found token in hidden input 'csrft'")
            return token
        return None

    def _extract_from_url(self, url: str) -> Optional[str]:
        """Check current URL query params."""
        for param in ['ert', 'rt']:
            match = re.search(f'[?&]{param}=([^&#]+)', url)
            if match:
                self.token_param = param
                token = unquote(match.group(1))
                logger.info(f"[{self.operator}] Found token '{token}' in URL param '{param}'")
                return token
        return None

    def _extract_from_source(self, html: str) -> Optional[str]:
        """Regex to find assignment in source code or script URLs."""
        # Check assignment: var ert = '...';
        for param in ['ert', 'rt']:
            match = re.search(rf'{param}["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
            if match:
                self.token_param = param
                token = unquote(match.group(1))
                logger.info(f"[{self.operator}] Found token in source code for param '{param}'")
                return token

        # Check for URLs in source
        for param in ['ert', 'rt']:
            match = re.search(rf'[?&]{param}=([^"\'&>]+)', html)
            if match:
                self.token_param = param
                token = unquote(match.group(1))
                logger.info(f"[{self.operator}] Found token in source URL for param '{param}'")
                return token
        return None

    def _extract_from_cookies(self, cookies: Any) -> Optional[str]:
        """Check cookies for token."""
        for param in ['ert', 'rt']:
            if param in cookies:
                self.token_param = param
                token = cookies[param]
                logger.info(f"[{self.operator}] Found token in cookie '{param}'")
                return token
        return None

    def get_token(self) -> Optional[str]:
        """Extract session token (ert or rt) from the portal."""
        try:
            url = f"{self.base_url}?appmode=outage"
            logger.info(f"[{self.operator}] Fetching token from {url}")
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"[{self.operator}] Failed to load portal: {response.status_code}")
                return None

            # Sequential extraction attempts to reduce cognitive complexity
            token = self._extract_from_input(response.text)
            if not token:
                token = self._extract_from_url(response.url)
            if not token:
                token = self._extract_from_source(response.text)
            if not token:
                token = self._extract_from_cookies(response.cookies)

            if token:
                self._token = token
                return token
                    
            logger.warning(f"[{self.operator}] Could not extract session token from {response.url}")
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
                            scraped_at=datetime.now(timezone.utc)
                        ))
            else:
                logger.warning(f"[{self.operator}] Failed to get messages from {url}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching messages: {e}")
            
        return outages

    def get_area_tickets(self, bbox: Dict[str, float], services: str) -> List[RawOutage]:
        """Get area tickets (outages) for a bounding box."""
        outages = []
        token = self._token or self.get_token()
        
        if not token:
            logger.warning(f"[{self.operator}] No token found, trying request without authentication")

        try:
            url = f"{self.base_url}/Fault/AreaTicketList"
            params = { **bbox, 'services': services }
            if token:
                params[self.token_param] = token
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                self._process_ticket_response(response, url, outages)
            else:
                logger.warning(f"[{self.operator}] Failed to get area tickets: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching area tickets: {e}")
            
        return outages

    def _process_ticket_response(self, response, url, outages):
        """Helper to process JSON ticket list."""
        if not response.text.strip():
            return
        try:
            tickets = response.json()
            if isinstance(tickets, list):
                for ticket in tickets:
                    outages.append(RawOutage(
                        operator=self.operator,
                        source_url=url,
                        raw_data=ticket,
                        scraped_at=datetime.now(timezone.utc)
                    ))
        except ValueError:
            logger.warning(f"[{self.operator}] Invalid JSON from AreaTicketList")

    SERVICES = (
        "NR700_DATANSA,NR1800_DATANSA,NR2100_DATANSA,NR2600_DATANSA,NR3500_DATANSA,"
        "LTE700_DATA,LTE800_DATA,LTE900_DATA,LTE1800_DATA,LTE2100_DATA,LTE2600_DATA,"
        "GSM900_VOICE,GSM1800_VOICE"
    )

    def get_admin_areas(self) -> List[Dict]:
        """Get list of administrative areas (regions/counties)."""
        token = self._token or self.get_token()
        try:
            url = f"{self.base_url}/Fault/AdminAreaList"
            params = {"services": self.SERVICES}
            if token:
                params[self.token_param] = token
            self.session.headers.update({"Referer": f"{self.base_url}?appmode=outage"})
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200 and response.text.strip():
                areas = response.json()
                if isinstance(areas, list):
                    logger.info(f"[{self.operator}] Got {len(areas)} admin areas")
                    return areas
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching admin areas: {e}")
        return []

    def get_region_faults(self, region_id: str) -> List[RawOutage]:
        """Get specific faults for a given region."""
        outages = []
        token = self._token or self.get_token()
        try:
            url = f"{self.base_url}/Fault/RegionFaultList"
            data = {'regionId': region_id}
            if token:
                data[self.token_param] = token
            
            response = self.session.post(url, data=data, timeout=15)
            if response.status_code == 200:
                faults = response.json()
                if isinstance(faults, list):
                    for fault in faults:
                        outages.append(RawOutage(
                            operator=self.operator,
                            source_url=url,
                            raw_data=fault,
                            scraped_at=datetime.now(timezone.utc)
                        ))
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching region faults: {e}")
        return outages
