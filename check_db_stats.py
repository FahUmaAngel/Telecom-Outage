import sqlite3
import sys

def check_db(db_path):
    print(f"Checking database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        if ('outages',) in tables:
            cursor.execute("SELECT count(*) FROM outages;")
            count = cursor.fetchone()[0]
            print(f"Total outages: {count}")
            
            cursor.execute("SELECT strftime('%Y-%m', start_time) as month, count(*) FROM outages GROUP BY month ORDER BY month DESC LIMIT 20;")
            months = cursor.fetchall()
            print("Outages by month (top 20):")
            for m, c in months:
                print(f"  {m}: {c}")
                
            cursor.execute("""
                SELECT o.name, count(*) 
                FROM outages ot 
                JOIN operators o ON ot.operator_id = o.id 
                GROUP BY o.name;
            """)
            operators = cursor.fetchall()
            print("Outages by operator:")
            for op, count in operators:
                print(f"  {op}: {count}")
        else:
            print("Table 'outages' not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "telecom_outage.db"
    check_db(db)
