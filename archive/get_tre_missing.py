import sqlite3
db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
try:
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    query = """
    SELECT o.incident_id, o.location 
    FROM outages o 
    JOIN operators op ON o.operator_id = op.id 
    WHERE op.name = 'tre' AND (o.latitude IS NULL OR o.longitude IS NULL)
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    with open('tre_missing.txt', 'w', encoding='utf-8') as f:
        f.write(f'Tre incidents missing coords: {len(rows)}\n')
        for r in rows:
            f.write(f'- ID: {r[0]} | Location: {r[1]}\n')
    print('Query successful. Output written to tre_missing.txt')
except Exception as e:
    print(f'Error: {e}')
