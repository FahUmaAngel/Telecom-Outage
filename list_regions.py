import sqlite3
import json

def get_regions():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM regions")
    regions = []
    for row in cur.fetchall():
        rid, name_json = row
        try:
            name_dict = json.loads(name_json)
            sv_name = name_dict.get('sv')
            regions.append((rid, sv_name))
        except:
            regions.append((rid, name_json))
    conn.close()
    return regions

if __name__ == "__main__":
    regions = get_regions()
    for r in regions:
        print(r)
