import sqlite3

def main():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT location, count(*)
        FROM outages
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'telia')
        GROUP BY location
        ORDER BY count(*) DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    
    print("Top 20 Telia Locations:")
    for r in rows:
        print(f"{r[0]:<40} {r[1]}")
        
    cur.execute("""
        SELECT count(*)
        FROM outages
        WHERE operator_id = (SELECT id FROM operators WHERE name = 'telia')
        AND location LIKE '%Unknown%'
    """)
    unknowns = cur.fetchone()[0]
    print(f"\nTotal Telia incidents containing 'Unknown': {unknowns}")

if __name__ == "__main__":
    main()
