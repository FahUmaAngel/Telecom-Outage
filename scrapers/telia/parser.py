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

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.translation import create_bilingual_text, SWEDISH_CITIES, SWEDISH_COUNTIES

logger = logging.getLogger(__name__)


def parse_telia_html(html_content: str) -> List[Dict]:
    """
    Parse Telia's HTML to extract outage information.
    
    Args:
        html_content: Raw HTML from Telia's outage page
        
    Returns:
        List of dictionaries containing raw outage data
    """
    if not html_content:
        logger.warning("Empty HTML content provided")
        return []
    
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        outages = []
        
        # Look for outage cards/items in the HTML
        # Note: This is a placeholder - actual selectors need to be determined
        # by inspecting the real Telia website structure
        
        # Try to find outage containers
        outage_containers = soup.find_all(['div', 'article', 'section'], 
                                         class_=re.compile(r'outage|incident|drift|störning', re.I))
        
        if not outage_containers:
            logger.info("No outage containers found with common class names")
            # Try alternative approach - look for specific text patterns
            outage_containers = soup.find_all(text=re.compile(r'störning|drift|incident', re.I))
            if outage_containers:
                logger.info(f"Found {len(outage_containers)} potential outage mentions")
        
        for container in outage_containers:
            try:
                outage_data = extract_outage_from_container(container)
                if outage_data:
                    outages.append(outage_data)
            except Exception as e:
                logger.error(f"Error parsing outage container: {e}")
                continue
        
        logger.info(f"Parsed {len(outages)} outages from Telia HTML")
        return outages
        
    except Exception as e:
        logger.error(f"Error parsing Telia HTML: {e}")
        return []


def extract_outage_from_container(container) -> Optional[Dict]:
    """
    Extract outage information from a single container element.
    
    Args:
        container: BeautifulSoup element containing outage info
        
    Returns:
        Dictionary with outage data or None
    """
    try:
        # This is a template - actual extraction logic depends on Telia's HTML structure
        outage = {
            'raw_html': str(container),
            'text_content': container.get_text(strip=True) if hasattr(container, 'get_text') else str(container)
        }
        
        # Try to extract structured data
        if hasattr(container, 'find'):
            # Look for title/heading
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'strong'])
            if title_elem:
                outage['title'] = title_elem.get_text(strip=True)
            
            # Look for description
            desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|text|content', re.I))
            if desc_elem:
                outage['description'] = desc_elem.get_text(strip=True)
            
            # Look for location
            loc_elem = container.find(text=re.compile(r'plats|ort|område|location', re.I))
            if loc_elem:
                outage['location'] = loc_elem.strip()
            
            # Look for status
            status_elem = container.find(text=re.compile(r'status|åtgärd|löst|aktiv', re.I))
            if status_elem:
                outage['status'] = status_elem.strip()
        
        # Only return if we found some meaningful data
        if len(outage) > 2:  # More than just raw_html and text_content
            return outage
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting outage data: {e}")
        return None


def parse_telia_json(json_data: dict) -> List[Dict]:
    """
    Parse JSON data from Telia API (if they have one).
    
    Args:
        json_data: JSON response from Telia API
        
    Returns:
        List of dictionaries containing raw outage data
    """
    try:
        outages = []
        
        # This is a placeholder - actual structure depends on Telia's API
        if isinstance(json_data, dict):
            # Look for common JSON structures
            for key in ['outages', 'incidents', 'data', 'items', 'results']:
                if key in json_data and isinstance(json_data[key], list):
                    outages = json_data[key]
                    break
        elif isinstance(json_data, list):
            outages = json_data
        
        logger.info(f"Parsed {len(outages)} outages from Telia JSON")
        return outages
        
    except Exception as e:
        logger.error(f"Error parsing Telia JSON: {e}")
        return []


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample HTML
    sample_html = """
    <div class="outage-item">
        <h3>Mobilnätet störning</h3>
        <p>Störning i mobilnätet i Stockholm området</p>
        <span>Status: Aktiv</span>
    </div>
    """
    
    outages = parse_telia_html(sample_html)
    print(f"Found {len(outages)} outages in sample HTML")
    for outage in outages:
        print(outage)
