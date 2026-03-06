import sqlite3

def check_lyca_end_dates():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Get Lycamobile ID
    cur.execute("SELECT id FROM operators WHERE name = 'lycamobile'")
    row = cur.fetchone()
    if not row:
        print("Lycamobile operator not found.")
        return
    lyca_id = row[0]
    
    # Count without end_time
    cur.execute("SELECT count(*) FROM outages WHERE operator_id = ? AND end_time IS NULL", (lyca_id,))
    no_end_time = cur.fetchone()[0]
    
    # Count without both
    cur.execute("SELECT count(*) FROM outages WHERE operator_id = ? AND end_time IS NULL AND estimated_fix_time IS NULL", (lyca_id,))
    no_both = cur.fetchone()[0]
    
    # Total Lyca
    cur.execute("SELECT count(*) FROM outages WHERE operator_id = ?", (lyca_id,))
    total = cur.fetchone()[0]
    
    print(f"Total Lycamobile outages: {total}")
    print(f"Lycamobile without end_time: {no_end_time}")
    print(f"Lycamobile without both end_time and estimated_fix_time: {no_both}")
    
    conn.close()

if __name__ == "__main__":
    check_lyca_end_dates()
