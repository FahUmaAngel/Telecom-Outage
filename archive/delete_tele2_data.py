import sqlite3

def delete_tele2_data():
    db_path = 'd:/94 FAH works/Telecom-Outage/telecom_outage.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get Tele2 operator ID
        cursor.execute("SELECT id FROM operators WHERE name = 'tele2'")
        res = cursor.fetchone()
        if not res:
            print("Tele2 operator not found in database.")
            return
            
        op_id = res[0]
        print(f"Tele2 Operator ID identified: {op_id}")
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = ?", (op_id,))
        count = cursor.fetchone()[0]
        print(f"Found {count} records associated with Tele2 in 'outages' table.")
        
        if count == 0:
            print("No records to delete.")
            return

        # Find associated raw_data IDs
        cursor.execute("SELECT raw_data_id FROM outages WHERE operator_id = ?", (op_id,))
        raw_ids = [r[0] for r in cursor.fetchall() if r[0] is not None]
        
        # Delete from outages
        print(f"Deleting {count} records from 'outages'...")
        cursor.execute("DELETE FROM outages WHERE operator_id = ?", (op_id,))
        
        # Delete from raw_data
        if raw_ids:
            print(f"Deleting {len(raw_ids)} associated records from 'raw_data'...")
            # Use chunks for safety if list is huge
            placeholders = ','.join(['?'] * len(raw_ids))
            cursor.execute(f"DELETE FROM raw_data WHERE id IN ({placeholders})", raw_ids)
            
        # Commit and Vacuum
        conn.commit()
        print("Committing changes and performing VACUUM...")
        cursor.execute("VACUUM")
        
        print(f"Successfully deleted all Tele2 data ({count} outages).")
        
    except Exception as e:
        print(f"Error during deletion: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    delete_tele2_data()
