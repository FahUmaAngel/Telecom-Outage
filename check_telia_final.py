import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('telecom_outage.db')
        c = conn.cursor()
        c.execute("SELECT incident_id, location, operator FROM outages WHERE operator = 'telia' ORDER BY id DESC LIMIT 20")
        rows = c.fetchall()
        print("ID | Location | Operator")
        print("-" * 30)
        for r in rows:
            print(f"{r[0]} | {r[1]} | {r[2]}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
