import sqlite3
import json

def check():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Check remaining Sverige/Unknown for lycamobile
    cursor.execute("""
        SELECT id, incident_id, location, title
        FROM outages 
        WHERE operator_id = (SELECT id FROM operators WHERE name="lycamobile")
        AND location IN ('Sverige', 'Unknown', 'sweden', 'unknown')
        ORDER BY id DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    print(f"Remaining Sverige/Unknown for Lycamobile: {len(rows)}")
    for r in rows:
        outage_id, incident_id, location, title_json = r
        try:
            title_sv = json.loads(title_json).get('sv', '') if title_json else ''
        except:
            title_sv = str(title_json)
        print(f"  ID:{outage_id} incident:{incident_id} loc:{location} title:{title_sv[:60]}")
    
    conn.close()

if __name__ == '__main__':
    check()
