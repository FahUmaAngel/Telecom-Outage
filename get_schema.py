import sqlite3
conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(outages);")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
