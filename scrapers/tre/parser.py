"""
Tre (3) parser.
Parses Next.js JSON to find outage information.
"""
from typing import List, Dict, Optional
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_tre_outages(raw_outages: List) -> List[Dict]:
    parsed = []
    
    for raw in raw_outages:
        try:
            data = raw.raw_data if hasattr(raw, 'raw_data') else raw
            
            # Navigate to content blocks
            # Based on inspection: props.pageProps.page.blocks
            try:
                props = data.get('props', {}).get('pageProps', {})
                page = props.get('page', {})
                blocks = page.get('blocks', [])
                
                for block in blocks:
                    # Look for content that resembles outages (text blocks)
                    items = block.get('items', [])
                    for item in items:
                        text = item.get('text', '')
                        if not text:
                            text = item.get('notificationMessage', '')
                        
                        if text and ('Arbete startar' in text or 'påverka täckning' in text or 'Driftstörning' in text or 'Senast uppdaterat' in text):
                            # This is likely the planned works block
                            logger.info("Found matching Tre text block, parsing details...")
                            parsed.extend(parse_markdown_text(text))
                            
            except Exception as e:
                logger.warning(f"Error navigating Tre JSON: {e}")
                
        except Exception as e:
            logger.error(f"Error parsing Tre outage: {e}")
            
    return parsed

def parse_markdown_text(text: str) -> List[Dict]:
    """
    Parse Tre's markdown-like outage list.
    Format:
    ### __City__
    - __Arbete startar:__ YYYY-MM-DD Kl HH:MM
    - __Arbete klart:__ YYYY-MM-DD Kl HH:MM
    - __Beskrivning:__ ...
    """
    outages = []
    
    # Split by location header (### __City__)
    # Regex to find these blocks
    # We'll use split to separate them, but keep the delimiter
    
    # Pattern to match: ### __City__
    # But since it's a long string, let's just find all matches and their indices
    
    # Simple strategy: Split by "### "
    chunks = text.split('### ')
    
    for chunk in chunks:
        if not chunk.strip():
            continue
            
        try:
            outage = {}
            lines = chunk.strip().split('\n')
            
            # First line is usually location: "__City__"
            location_line = lines[0].replace('__', '').strip()
            if location_line:
                outage['location'] = location_line
            
            # Parse other lines
            for line in lines[1:]:
                clean_line = line.replace('__', '').strip('- ').strip()
                
                if 'Arbete startar:' in clean_line:
                    time_str = clean_line.split('Arbete startar:')[1].strip()
                    outage['start_time'] = parse_tre_date(time_str)
                elif 'Arbete klart:' in clean_line:
                    time_str = clean_line.split('Arbete klart:')[1].strip()
                    outage['end_time'] = parse_tre_date(time_str)
                elif 'Senast uppdaterat:' in clean_line:
                    time_str = clean_line.split('Senast uppdaterat:')[1].strip()
                    # Use update time as start time for these warnings
                    outage['start_time'] = parse_tre_date(time_str)
                elif 'Beskrivning:' in clean_line:
                    desc_text = clean_line.split('Beskrivning:')[1].strip()
                    outage['description'] = desc_text
                    
                    # Extract affected services from text
                    services = []
                    lower_desc = desc_text.lower()
                    if '5g' in lower_desc: services.append('5G')
                    if '4g' in lower_desc: services.append('4G')
                    if '3g' in lower_desc: services.append('3G')
                    if '2g' in lower_desc: services.append('2G')
                    if 'data' in lower_desc or 'surf' in lower_desc or 'internet' in lower_desc: services.append('Mobile Data')
                    if 'samtal' in lower_desc or 'röst' in lower_desc or 'telefoni' in lower_desc: services.append('Voice')
                    if 'sms' in lower_desc: services.append('SMS')
                    
                    if not services: services.append('Mobile Network')
                    outage['affected_services'] = list(set(services))
            
            if outage.get('location') and (outage.get('start_time') or outage.get('end_time')):
                # Generate an ID based on location and time
                t_val = outage.get('start_time') or outage.get('end_time')
                outage['id'] = f"tre_{outage['location']}_{t_val.replace(' ','_')}"
                outages.append(outage)
                
        except Exception as e:
            logger.warning(f"Error parsing text chunk: {e}")
            
    return outages

def parse_tre_date(date_str: str) -> Optional[str]:
    # Format: 2025-12-15 Kl 00:00
    try:
        # Remove 'Kl' and extra spaces, case insensitive
        clean = date_str.lower().replace('kl', '').strip()
        # Parse
        dt = datetime.strptime(clean, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None
