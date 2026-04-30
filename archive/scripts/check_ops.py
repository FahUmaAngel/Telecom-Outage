import sqlite3
conn = sqlite3.connect('telecom_outage.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM operators;")
print(cursor.fetchall())
conn.close()
