import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'sv-SE,sv;q=0.9'}

print("=== TELENOR ===")
try:
    r = requests.get('https://www.telenor.se/support/driftinformation/driftstorningar-pa-mobilnatet/', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text()
    print('Status:', r.status_code, '| Length:', len(text))
    counties = ['Stockholms', 'Skane', 'Goteborg', 'Uppsala', 'Hallands', 'Blekinge', 'Malmo']
    found = [c for c in counties if c.lower() in text.lower()]
    print('Counties found:', found)
    # Print relevant parts
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 20 and any(c.lower() in line.lower() for c in counties + ['driftstorning', 'incident', 'lan']):
            print(' -', line[:120])
except Exception as e:
    print('ERROR:', e)

print()
print("=== TRE ===")
try:
    r = requests.get('https://www.tre.se/varfor-tre/tackning/driftstorningar', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text()
    print('Status:', r.status_code, '| Length:', len(text))
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 10 and any(kw in line.lower() for kw in ['lan', 'stockholm', 'goteborg', 'skane', 'planerat', 'driftstorn']):
            print(' -', line[:120])
except Exception as e:
    print('ERROR:', e)
