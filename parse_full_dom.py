from bs4 import BeautifulSoup
import re
import sqlite3
import sys
import os

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

def parse_dom():
    try:
        with open('telia_full_dom.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print("Could not read DOM file:", e)
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Process all rows in document order.
    # The header row has a <td> with "län" and "Visa område".
    # The incident rows contain "INCSE".
    
    current_region = None
    incidents = {}
    
    rows = soup.find_all('tr')
    for row in rows:
        text = row.get_text(separator=' ', strip=True)
        
        # Check if it's a regional header
        if 'län' in text and 'Visa område' in text:
            # The region is usually the first td
            cells = row.find_all('td')
            if cells:
                current_region = cells[0].get_text(strip=True).replace('Visa område', '').strip()
            else:
                current_region = text.split('Visa område')[0].strip()
            continue
            
        # If not a header, see if it's an incident
        if 'INCSE' in text and current_region:
            # Find all INCSE in this row
            inc_ids = re.findall(r'INCSE\d+', text)
            for inc in set(inc_ids):
                # Don't overwrite if we already found it (just in case)
                if inc not in incidents:
                    incidents[inc] = current_region

    print(f"Total mapped incidents: {len(incidents)}")
    if not incidents:
        print("Regex check: Any INCSE in the whole HTML?")
        print(len(re.findall(r'INCSE\d+', html)))
        return
        
    # See if Örebro was found
    orebro_incs = [i for i, r in incidents.items() if 'Örebro' in r]
    print(f"Örebro Incidents found: {orebro_incs}")
    
    # Print summary
    from collections import Counter
    c = Counter(incidents.values())
    for region, count in c.most_common():
        print(f" - {region}: {count} incidents")
        
    # Update DB
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    updated = 0
    for inc_id, region in incidents.items():
        coords = get_county_coordinates(region, jitter=True)
        if coords:
            cursor.execute("""
                UPDATE outages
                SET location = ?, latitude = ?, longitude = ?
                WHERE incident_id = ? AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
            """, (region, coords[0], coords[1], inc_id))
        else:
            cursor.execute("""
                UPDATE outages
                SET location = ?
                WHERE incident_id = ? AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
            """, (region, inc_id))
        updated += cursor.rowcount
            
    conn.commit()
    conn.close()
    print(f"\nSuccessfully updated {updated} database records with exact regions.")

if __name__ == "__main__":
    parse_dom()
