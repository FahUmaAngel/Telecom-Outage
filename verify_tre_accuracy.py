"""
ตรวจสอบความถูกต้องของข้อมูล Tre:
1. ดึงข้อมูลสดจากเว็บ Tre ปัจจุบัน
2. เปรียบเทียบกับข้อมูลใน Database
3. รายงานผลสรุป
"""
import requests
from bs4 import BeautifulSoup
import json
import sqlite3

TRE_URL = "https://www.tre.se/varfor-tre/tackning/driftstorningar"

def fetch_live_tre():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    try:
        resp = session.get(TRE_URL, timeout=15)
        if resp.status_code != 200:
            print(f"HTTP Error: {resp.status_code}")
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            print("No __NEXT_DATA__ found on page.")
            return []
        
        data = json.loads(next_data.string)
        
        # Try to find the actual content with outages
        props = data.get('props', {}).get('pageProps', {})
        page = props.get('page', {})
        blocks = page.get('blocks', [])
        
        live_incidents = []
        for block in blocks:
            for item in block.get('items', []):
                text = item.get('text', item.get('notificationMessage', ''))
                if text and ('Arbete startar' in text or 'Driftstörning' in text or 'Senast uppdaterat' in text):
                    # Try to parse from the markdown text
                    chunks = text.split('### ')
                    for chunk in chunks:
                        if chunk.strip():
                            lines = chunk.strip().split('\n')
                            loc = lines[0].replace('__', '').strip() if lines else ''
                            if loc:
                                inc = {'location': loc, 'raw_text': chunk[:200]}
                                for line in lines[1:]:
                                    clean = line.replace('__', '').strip('- ').strip()
                                    if 'Arbete startar:' in clean:
                                        inc['start'] = clean.split('Arbete startar:')[1].strip()
                                    elif 'Arbete klart:' in clean:
                                        inc['end'] = clean.split('Arbete klart:')[1].strip()
                                    elif 'Beskrivning:' in clean:
                                        inc['description'] = clean.split('Beskrivning:')[1].strip()[:100]
                                live_incidents.append(inc)
        return live_incidents
    except Exception as e:
        print(f"Error fetching Tre: {e}")
        return []

def check_db():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT o.incident_id, o.status, o.location, o.start_time, o.end_time
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'tre' AND o.status != 'resolved'
        ORDER BY o.start_time DESC
        LIMIT 50
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def main():
    print("=" * 60)
    print("  ข้อมูล LIVE จากเว็บ Tre")
    print("=" * 60)
    live = fetch_live_tre()
    if live:
        for i, inc in enumerate(live, 1):
            print(f"\nLive #{i}:")
            print(f"  Location : {inc.get('location')}")
            print(f"  Start    : {inc.get('start', 'N/A')}")
            print(f"  End      : {inc.get('end', 'N/A')}")
            print(f"  Desc     : {inc.get('description', 'N/A')}")
    else:
        print("ไม่พบข้อมูล Incident บนเว็บ Tre ณ ขณะนี้")

    print("\n" + "=" * 60)
    print("  ข้อมูล Active ใน Database")
    print("=" * 60)
    db_rows = check_db()
    if db_rows:
        for row in db_rows:
            inc_id, status, loc, start, end = row
            print(f"\nDB ID : {inc_id}")
            print(f"  Status   : {status}")
            print(f"  Location : {loc}")
            print(f"  Start    : {start}")
            print(f"  End      : {end}")
    else:
        print("ไม่พบข้อมูล Active Tre ใน Database")
    
    print(f"\n\nสรุป: ข้อมูล Live จากเว็บ = {len(live)} รายการ  |  Active DB ที่ไม่ใช่ resolved = {len(db_rows)} รายการ")

if __name__ == '__main__':
    main()
