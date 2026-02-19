
import sqlite3
import json

def verify():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get top 3 outages
    cursor.execute('SELECT op.name, o.title, r.data, o.affected_services FROM outages o JOIN operators op ON o.operator_id = op.id JOIN raw_data r ON o.raw_data_id = r.id ORDER BY o.id DESC LIMIT 3')
    rows = cursor.fetchall()
    
    print("=== DATA VERIFICATION (Sample: Last 3 Outages) ===")
    for r in rows:
        print(f"Operator: {r[0]}")
        print(f"Title: {r[1]}")
        print(f"Displayed Services: {r[3]}")
        # Try to find description in raw data
        raw_data = json.loads(r[2])
        raw_outage = raw_data.get('raw_outage', raw_data.get('raw', {}))
        desc = raw_outage.get('description', 'N/A')
        print(f"Raw Description: {desc[:100]}...")
        print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    verify()
