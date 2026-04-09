import sqlite3
import json

def inspect():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT rd.id, rd.data 
        FROM raw_data rd 
        WHERE rd.operator = 'tre' 
        ORDER BY rd.id DESC 
        LIMIT 1
    ''')
    row = cur.fetchone()
    if row:
        data = json.loads(row[1])
        # Find the actual outage data inside __NEXT_DATA__
        # Usually data['props']['pageProps']
        try:
            print("Keys at root:", data.keys())
            pageProps = data.get('props', {}).get('pageProps', {})
            print("Keys in pageProps:", pageProps.keys())
            
            # Print a snippet of disturbances
            disturbances = pageProps.get('disturbances', [])
            print(f"Found {len(disturbances)} disturbances.")
            if disturbances:
                print("First disturbance:", json.dumps(disturbances[0], indent=2, ensure_ascii=False))
        except Exception as e:
            print("Error parsing Tre data", e)
    conn.close()

if __name__ == '__main__':
    inspect()
