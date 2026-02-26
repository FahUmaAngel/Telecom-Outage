from bs4 import BeautifulSoup
import json

def analyze():
    with open('lyca_selenium_final.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check what h6 headings are present
    headings = soup.find_all('h6')
    print("Headings:")
    for h in headings:
        print(f" - {h.text.strip()}")
        
    print("\nTables:")
    tables = soup.find_all('table')
    print(f"Total tables: {len(tables)}")
    
    for i, t in enumerate(tables):
        print(f"\nTable {i}:")
        print(f"Class: {t.get('class')}")
        headers = [th.text.strip() for th in t.find_all('th')]
        print(f"Headers: {headers}")
        
        # Are there incident IDs in this table?
        rows = t.find_all('tr')
        incident_rows = 0
        for r in rows:
            cells = r.find_all('td')
            if cells and cells[0].text.strip().isdigit() and len(cells[0].text.strip()) == 8:
                incident_rows += 1
        print(f"Rows looking like incidents: {incident_rows}")

if __name__ == '__main__':
    analyze()
