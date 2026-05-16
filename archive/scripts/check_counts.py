import sqlite3

def check_data():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Check Telia (id=1)
    print("--- Telia (ID 1) ---")
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 1")
    print("Total Telia outages:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 1 AND start_time IS NOT NULL AND start_time != ''")
    print("With start_time:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 1 AND estimated_fix_time IS NOT NULL AND estimated_fix_time != ''")
    print("With estimated_fix_time:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 1 AND start_time IS NOT NULL AND start_time != '' AND estimated_fix_time IS NOT NULL AND estimated_fix_time != ''")
    print("With Both (AND NOT EMPTY):", cursor.fetchone()[0])

    # Check Lycamobile (ID 3)
    print("\n--- Lycamobile (ID 3) ---")
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 3")
    print("Total Lycamobile outages:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = 3 AND start_time IS NOT NULL AND start_time != '' AND estimated_fix_time IS NOT NULL AND estimated_fix_time != ''")
    print("With Both (AND NOT EMPTY):", cursor.fetchone()[0])

    conn.close()

if __name__ == "__main__":
    check_data()
