import requests
import sqlite3

def check_detail():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    
    # Let's get a few Stockholms län IDs
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT incident_id FROM outages 
        WHERE location = 'Stockholms län' AND operator_id = (SELECT id FROM operators WHERE name = 'telia')
        LIMIT 5
    """)
    ids = [r[0] for r in cursor.fetchall()]
    
    for inc_id in ids:
        url = f"https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage&ticket={inc_id}"
        print(f"Fetching {url}")
        r = s.get(url)
        if 'Örebro' in r.text or 'Orebro' in r.text:
            print(f"FOUND ÖREBRO in {inc_id}!")
        if 'Stockholm' in r.text:
            print(f"Found Stockholm in {inc_id}!")
            
    conn.close()

if __name__ == "__main__":
    check_detail()
