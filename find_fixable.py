import sqlite3
import json
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.engine import extract_region_from_text
from scrapers.common.translation import SWEDISH_COUNTIES

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("SELECT id, title, description FROM outages WHERE location = 'Unknown'")
rows = cur.fetchall()

found = 0
for oid, title_str, desc_str in rows:
    try:
        title_data = json.loads(title_str)
        t_sv = title_data.get('sv', '')
        
        desc_data = json.loads(desc_str)
        d_sv = desc_data.get('sv', '')
        
        context = f"{t_sv} {d_sv}"
        county = extract_region_from_text(context, SWEDISH_COUNTIES)
        
        if county:
            print(f"ID {oid}: Found '{county}' in context '{context[:50]}...'")
            found += 1
    except:
        continue

print(f"Total fixable: {found}")
conn.close()
