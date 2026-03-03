from bs4 import BeautifulSoup
import sqlite3
import sys
import os

sys.path.append(os.getcwd())
from scrapers.common.geocoding import get_county_coordinates

def fix_all_regions():
    try:
        with open('telia_selenium_v3_final.html', 'r', encoding='utf-8') as f:
            html = f.write()
    except:
        with open('telia_selenium_v3_final.html', 'r', encoding='utf-8') as f:
            html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # The structure usually has region headers and tables
    # Let's see if we can find tables and their preceding headings or parent containers
    # E.g., <div class="accordion-item">... region name ... <table>...</table></div>
    
    incident_region_map = {}
    
    # Try finding all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for table in tables:
        # try to find the region name nearby
        # look at the table's parents or previous siblings
        region_name = ""
        parent = table.find_parent('div', class_=lambda c: c and 'accordion' in c.lower())
        if not parent:
             # Just look at the text before the table
             prev = table.find_previous(['h2', 'h3', 'h4', 'th', 'button'])
             if prev:
                 region_name = prev.get_text(strip=True).replace('Visa område', '').strip()
        else:
             # Try to find a header button in the accordion
             header = parent.find(['button', 'h3', 'h4'])
             if header:
                 region_name = header.get_text(strip=True).replace('Visa område', '').strip()
                 
        if not region_name:
            # Maybe inside the table itself there's a header?
            # Or the previous row? Let's just grab the text of the closest button
            btn = table.find_previous(string=lambda text: "Visa område" in str(text))
            if btn:
                 region_name = btn.replace('Visa område', '').strip()

        if not region_name:
            # Generic approach: find the first <td> in the closest preceding <tr> that is not in THIS table
            # Too complex. Let's just find the generic text.
            pass

        # Now get incidents in this table
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                id_cell = cells[0].get_text(strip=True)
                import re
                inc_id_match = re.search(r'INCSE\d+', id_cell)
                if inc_id_match and region_name:
                    incident_region_map[inc_id_match.group()] = region_name

    print("Region mapping found from HTML:")
    for k, v in incident_region_map.items():
        if 'Stockholm' not in v and 'Västra' not in v:
            print(f"{k} -> {v}")

    # Now fix the DB
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    updated = 0
    for inc_id, region in incident_region_map.items():
        if not region: continue
        # Clean up region
        if '\n' in region:
            region = region.split('\n')[0].strip()
            
        # We only really care if it has 'län'
        if 'län' in region:
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
    
    print(f"\nUpdated {updated} records in the database based on HTML mapping.")

if __name__ == "__main__":
    fix_all_regions()
