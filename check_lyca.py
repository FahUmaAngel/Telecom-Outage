import sqlite3
import json

def check():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, incident_id, location FROM outages WHERE operator_id = (SELECT id FROM operators WHERE name="lycamobile") ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    check()
