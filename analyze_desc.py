import sqlite3
import json
from collections import Counter

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("SELECT description FROM outages WHERE description IS NOT NULL")
rows = cur.fetchall()

descriptions = []
for r in rows:
    try:
        desc = json.loads(r[0])
        sv = desc.get('sv', '')
        if sv:
            # Normalize a bit to find common patterns
            # Replace numbers/specific IDs to see the "template"
            import re
            template = re.sub(r'\d+', 'X', sv)
            descriptions.append(template)
    except:
        pass

# Show 50 most common templates
counter = Counter(descriptions)
print("COMMON DESCRIPTION TEMPLATES:")
for desc, count in counter.most_common(50):
    print(f"[{count}] {desc}")

conn.close()
