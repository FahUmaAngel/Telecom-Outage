import sqlite3, json
target_ids = ['INCSE0504255', 'INCSE0500172', 'INCSE0508251', 'INCSE0504462', 'INCSE0505843', 'INCSE0499021', 'INCSE0504462', 'INCSE0506219', 'INCSE0507801', 'INCSE0498666', 'INCSE0505464', 'INCSE0505881', 'INCSE0505885', 'INCSE0505922', 'INCSE0506172', 'INCSE0502696', 'INCSE0502697', 'INCSE0502694', 'INCSE0508167', 'INCSE0508249', 'INCSE0508259', 'INCSE0508273', 'INCSE0505543', 'INCSE0507001', 'INCSE0497828', 'INCSE0498666', 'INCSE0500172', 'INCSE0505870', 'INCSE0505881', 'INCSE0505885', 'INCSE0505922', 'INCSE0505021', 'INCSE0497843', 'INCSE0508289', 'INCSE0505543', 'INCSE0499021', 'INCSE0506784', 'INCSE0502566']
found = {}

try:
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    print('DB Connected. Scanning for IDs...')
    
    for tid in target_ids:
        cursor.execute("SELECT data FROM raw_data WHERE data LIKE ?", ('%' + tid + '%',))
        for row in cursor.fetchall():
            data_str = row[0]
            try:
                items = json.loads(data_str)
                if isinstance(items, list):
                    for item in items:
                        if item.get('ExternalId') == tid or item.get('incidentId') == tid:
                            found[tid] = item
                            print(f'Found DB payload for {tid}')
                            break
                elif isinstance(items, dict):
                    # sometimes it's wrapped
                    for k, v in items.items():
                        if isinstance(v, dict) and (v.get('ExternalId') == tid or v.get('incidentId') == tid):
                            found[tid] = v
                            print(f'Found DB payload for {tid}')
                            break
            except Exception as e:
                pass
            if tid in found:
                break
    
    conn.close()
except Exception as e:
    print('DB Error:', e)

print(f'\nFinished scanning DB. Found {len(found)} out of {len(set(target_ids))} target incidents in historical scraped data.')
with open('db_recovered_incidents.json', 'w', encoding='utf-8') as f:
    json.dump(found, f, ensure_ascii=False, indent=2)
