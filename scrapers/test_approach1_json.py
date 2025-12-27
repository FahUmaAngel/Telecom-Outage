"""
Approach 1: Parse JSON from __NEXT_DATA__ script tag
"""
import json
import re
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_next_data(html_content: str) -> dict:
    """
    Extract JSON data from __NEXT_DATA__ script tag.
    
    Args:
        html_content: Raw HTML from Telia page
        
    Returns:
        Parsed JSON data or empty dict
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Find the __NEXT_DATA__ script tag
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not script_tag:
            logger.error("__NEXT_DATA__ script tag not found")
            return {}
        
        # Parse JSON content
        json_text = script_tag.string
        data = json.loads(json_text)
        
        logger.info("Successfully extracted __NEXT_DATA__")
        return data
        
    except Exception as e:
        logger.error(f"Error extracting __NEXT_DATA__: {e}")
        return {}


def find_outage_data_in_json(data: dict, path: list = None) -> list:
    """
    Recursively search for outage data in nested JSON.
    
    Args:
        data: JSON data to search
        path: Current path in JSON (for logging)
        
    Returns:
        List of potential outage data locations
    """
    if path is None:
        path = []
    
    findings = []
    
    if isinstance(data, dict):
        # Look for keys that might contain outage data
        outage_keywords = ['outage', 'incident', 'drift', 'störning', 'disruption']
        
        for key, value in data.items():
            current_path = path + [key]
            
            # Check if key contains outage-related keywords
            if any(keyword in str(key).lower() for keyword in outage_keywords):
                findings.append({
                    'path': ' -> '.join(current_path),
                    'data': value
                })
                logger.info(f"Found potential outage data at: {' -> '.join(current_path)}")
            
            # Recursively search nested structures
            findings.extend(find_outage_data_in_json(value, current_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = path + [f"[{i}]"]
            findings.extend(find_outage_data_in_json(item, current_path))
    
    return findings


if __name__ == "__main__":
    # Test with saved HTML
    with open('telia_raw_output.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    print("=" * 60)
    print("APPROACH 1: Parsing __NEXT_DATA__ JSON")
    print("=" * 60)
    
    # Extract JSON data
    next_data = extract_next_data(html)
    
    if next_data:
        print(f"\n✓ Successfully extracted __NEXT_DATA__")
        print(f"  Top-level keys: {list(next_data.keys())}")
        
        # Search for outage data
        print("\nSearching for outage-related data...")
        findings = find_outage_data_in_json(next_data)
        
        if findings:
            print(f"\n✓ Found {len(findings)} potential outage data locations:")
            for finding in findings[:5]:  # Show first 5
                print(f"\n  Path: {finding['path']}")
                print(f"  Data type: {type(finding['data'])}")
                if isinstance(finding['data'], (str, int, bool)):
                    print(f"  Value: {finding['data']}")
                elif isinstance(finding['data'], (list, dict)):
                    print(f"  Size: {len(finding['data'])} items")
        else:
            print("\n✗ No outage-related data found in __NEXT_DATA__")
            print("\nThis suggests that outage data is loaded dynamically after page load.")
        
        # Save extracted JSON for inspection
        with open('telia_next_data.json', 'w', encoding='utf-8') as f:
            json.dump(next_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved full JSON to: telia_next_data.json")
    else:
        print("\n✗ Failed to extract __NEXT_DATA__")
    
    print("\n" + "=" * 60)
    print("RESULT: Approach 1 - " + ("SUCCESS" if findings else "FAILED"))
    print("=" * 60)
