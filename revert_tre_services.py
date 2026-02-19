import sqlite3
import json

db_path = "telecom_outage.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Reverting Tre services to ['mobile']...")
    
    # Get Tre operator ID
    cursor.execute("SELECT id FROM operators WHERE name = 'tre'")
    row = cursor.fetchone()
    if not row:
        print("Tre operator not found.")
    else:
        tre_id = row[0]
        # Update Tre services to ["mobile"]
        cursor.execute(
            "UPDATE outages SET affected_services = ? WHERE operator_id = ?",
            (json.dumps(["mobile"]), tre_id)
        )
        print(f"Successfully updated {cursor.rowcount} records for Tre.")
        conn.commit()
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
