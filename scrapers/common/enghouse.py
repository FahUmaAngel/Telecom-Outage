import requests
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
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

    def get_token(self) -> Optional[str]:
        """Extract session token (ert or rt) from the portal."""
        try:
            # Usually the token is in the main page or in cookies/local storage logic
            # For Enghouse, it's often passed as a query param 'ert' or found in source
            url = f"{self.base_url}?appmode=outage"
            logger.info(f"[{self.operator}] Fetching token from {url}")
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                # 0. Check for <input id="csrft" value="...">
                match = re.search(r'id=["\']csrft["\']\s+value=["\']([^"\']+)["\']', response.text)
                if not match:
                    match = re.search(r'value=["\']([^"\']+)["\']\s+id=["\']csrft["\']', response.text)
                
                if match:
                    self._token = unquote(match.group(1))
                    logger.info(f"[{self.operator}] Found token in hidden input 'csrft'")
                    return self._token

                # 1. Check current URL query params (some sites redirect to a URL with the token)
                for param in ['ert', 'rt']:
                    match = re.search(f'[?&]{param}=([^&#]+)', response.url)
                    if match:
                        self._token = unquote(match.group(1))
                        self.token_param = param
                        logger.info(f"[{self.operator}] Found token '{self._token}' in URL param '{param}'")
                        return self._token

                # 2. Regex to find assignment in source code: var ert = '...'; or obj.rt = '...';
                for param in ['ert', 'rt']:
                    match = re.search(rf'{param}["\']?\s*[:=]\s*["\']([^"\']+)["\']', response.text)
                    if match:
                        self._token = unquote(match.group(1))
                        self.token_param = param
                        logger.info(f"[{self.operator}] Found token in source code for param '{param}'")
                        return self._token
                
                # 3. Check for URLs containing the token in the source (found in scripts)
                for param in ['ert', 'rt']:
                    match = re.search(rf'[?&]{param}=([^"\'&>]+)', response.text)
                    if match:
                        self._token = unquote(match.group(1))
                        self.token_param = param
                        logger.info(f"[{self.operator}] Found token in source URL for param '{param}'")
                        return self._token

                # 4. Check cookies
                for param in ['ert', 'rt']:
                    if param in response.cookies:
                        self._token = response.cookies[param]
                        self.token_param = param
                        logger.info(f"[{self.operator}] Found token in cookie '{param}'")
                        return self._token
                    
            logger.warning(f"[{self.operator}] Could not extract session token from {response.url}")
            return None
            
        except Exception as e:
            logger.error(f"[{self.operator}] Error extracting token: {e}")
            return None

    def get_messages(self) -> List[RawOutage]:
        """Get important messages (usually doesn't require token)."""
        outages = []
        try:
            # Note: /ImportantMessages/GetMessages usually doesn't need a token
            # But we check if it's needed based on operator if we fail
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
                logger.warning(f"[{self.operator}] Failed to get messages from {url}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching messages: {e}")
            
        return outages

    def get_area_tickets(self, bbox: Dict[str, float], services: str) -> List[RawOutage]:
        """Get area tickets (outages) for a bounding box."""
        outages = []
        # Try to get token, but proceed if we already have one
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
                params[self.token_param] = token
            
            logger.debug(f"[{self.operator}] Fetching tickets from {url} with params {params.keys()}")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                if not response.text.strip():
                     logger.warning(f"[{self.operator}] Empty response from AreaTicketList")
                     return outages

                try:
                    tickets = response.json()
                    if isinstance(tickets, list):
                        logger.info(f"[{self.operator}] Found {len(tickets)} tickets")
                        for ticket in tickets:
                            outages.append(RawOutage(
                                operator=self.operator,
                                source_url=url,
                                raw_data=ticket,
                                scraped_at=datetime.now()
                            ))
                except ValueError: # JSONDecodeError
                    logger.warning(f"[{self.operator}] Invalid JSON from AreaTicketList: {response.text[:100]}...")
            else:
                logger.warning(f"[{self.operator}] Failed to get area tickets from {url}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[{self.operator}] Error fetching area tickets: {e}")
            
        return outages

