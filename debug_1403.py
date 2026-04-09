import sqlite3
import json

conn = sqlite3.connect('telecom_outage.db')
cur = conn.cursor()
cur.execute("SELECT title, description, location FROM outages WHERE id = 1403")
row = cur.fetchone()
if row:
    title, desc, loc = row
    print("ID: 1403")
    print(f"Title: {title}")
    print(f"Type of Title: {type(title)}")
    print(f"Description: {desc}")
    print(f"Location: {loc}")
else:
    print("Outage 1403 not found.")
conn.close()
