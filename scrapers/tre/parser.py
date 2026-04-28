"""
Tre (3) parser.
Parses Next.js JSON to find outage information.
"""
from typing import List, Dict, Optional, Any
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

def _navigate_blocks(data: Dict) -> List[Dict]:
    """Helper to find content blocks in Tre's JSON structure."""
    try:
        props = data.get('props', {}).get('pageProps', {})
        return props.get('page', {}).get('blocks', [])
    except (AttributeError, TypeError):
        return []

def _is_outage_block(text: str) -> bool:
    """Check if a text block likely contains outage information."""
    if not text:
        return False
    keywords = ['Arbete startar', 'påverka täckning', 'Driftstörning', 'Senast uppdaterat', 'Aktuella störningar']
    return any(k in text for k in keywords)

def parse_tre_outages(raw_outages: List) -> List[Dict]:
    """Main parser for Tre's raw data."""
    parsed = []
    for raw in raw_outages:
        try:
            data = raw.raw_data if hasattr(raw, 'raw_data') else raw
            blocks = _navigate_blocks(data)
            
            for block in blocks:
                for item in block.get('items', []):
                    text = item.get('text', '') or item.get('notificationMessage', '')
                    if _is_outage_block(text):
                        logger.info(f"Found Tre outage block, parsing...")
                        parsed.extend(parse_markdown_text(text))
        except Exception as e:
            logger.error(f"Error parsing Tre outage: {e}")
    return parsed

def _extract_services(desc_text: str) -> List[str]:
    """Extract affected services from description text."""
    services = []
    lower_desc = desc_text.lower()
    mapping = {
        '5g': '5G', '4g': '4G', '3g': '3G', '2g': '2G',
        'surf': 'Mobile Data', 'data': 'Mobile Data', 'internet': 'Mobile Data',
        'samtal': 'Voice', 'röst': 'Voice', 'telefoni': 'Voice',
        'sms': 'SMS'
    }
    for kw, label in mapping.items():
        if kw in lower_desc:
            services.append(label)
    
    return list(set(services)) if services else ['Mobile Network']

def _parse_chunk_lines(lines: List[str], outage: Dict):
    """Process lines within a location chunk."""
    for line in lines[1:]:
        clean = line.replace('__', '').strip('- ').strip()
        
        if 'Arbete startar:' in clean:
            outage['start_time'] = parse_tre_date(clean.split('Arbete startar:')[1].strip())
        elif 'Arbete klart:' in clean:
            outage['end_time'] = parse_tre_date(clean.split('Arbete klart:')[1].strip())
        elif 'Senast uppdaterat:' in clean:
            outage['start_time'] = parse_tre_date(clean.split('Senast uppdaterat:')[1].strip())
        elif 'Beskrivning:' in clean:
            desc = clean.split('Beskrivning:')[1].strip()
            outage['description'] = desc
            outage['affected_services'] = _extract_services(desc)

def _generate_id(outage: Dict) -> str:
    """Generate a unique ID for the outage."""
    t_val = outage.get('start_time') or outage.get('end_time', 'unknown')
    raw_str = f"tre_{outage.get('location', 'unknown')}_{t_val.replace(' ', '_')}"
    hash_val = hashlib.sha256(raw_str.encode()).hexdigest()[:6].upper()
    return f"TRE-{hash_val}"

def parse_markdown_text(text: str) -> List[Dict]:
    """Parse Tre's markdown-like outage list."""
    outages = []
    chunks = text.split('### ')
    
    for chunk in chunks:
        if not chunk.strip():
            continue
            
        try:
            outage = {}
            lines = chunk.strip().split('\n')
            location = lines[0].replace('__', '').strip()
            if not location:
                continue
                
            outage['location'] = location
            _parse_chunk_lines(lines, outage)
            
            if outage.get('location') and (outage.get('start_time') or outage.get('end_time')):
                outage['id'] = _generate_id(outage)
                outages.append(outage)
        except Exception as e:
            logger.warning(f"Error parsing text chunk: {e}")
            
    return outages

def parse_tre_date(date_str: str) -> Optional[str]:
    """Parse Tre date format (YYYY-MM-DD Kl HH:MM)."""
    try:
        clean = date_str.lower().replace('kl', '').strip()
        dt = datetime.strptime(clean, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except (ValueError, AttributeError):
        return None
