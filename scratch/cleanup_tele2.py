"""Cleanup all Tele2 data from telecom_outage.db.

Deletes:
  - outages with operator_id = tele2
  - raw_data rows referenced by those outages
  - raw_data rows with operator='tele2'
  - the tele2 operator row itself

Finishes with VACUUM and prints summary.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'telecom_outage.db')

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM operators WHERE LOWER(name) = 'tele2'")
        row = c.fetchone()
        op_id = row[0] if row else None
        print(f"Tele2 operator id: {op_id}")

        # Counts before
        c.execute("SELECT COUNT(*) FROM raw_data WHERE LOWER(operator) = 'tele2'")
        raw_count = c.fetchone()[0]
        print(f"raw_data rows with operator='tele2': {raw_count}")

        outage_count = 0
        linked_raw_ids = []
        if op_id is not None:
            c.execute("SELECT COUNT(*) FROM outages WHERE operator_id = ?", (op_id,))
            outage_count = c.fetchone()[0]
            print(f"outages rows for tele2 operator: {outage_count}")

            c.execute("SELECT raw_data_id FROM outages WHERE operator_id = ? AND raw_data_id IS NOT NULL", (op_id,))
            linked_raw_ids = [r[0] for r in c.fetchall()]
            print(f"linked raw_data ids from outages: {len(linked_raw_ids)}")

        # Delete
        if op_id is not None:
            c.execute("DELETE FROM outages WHERE operator_id = ?", (op_id,))
            print(f"  deleted outages: {c.rowcount}")

            if linked_raw_ids:
                placeholders = ','.join(['?'] * len(linked_raw_ids))
                c.execute(f"DELETE FROM raw_data WHERE id IN ({placeholders})", linked_raw_ids)
                print(f"  deleted linked raw_data: {c.rowcount}")

        c.execute("DELETE FROM raw_data WHERE LOWER(operator) = 'tele2'")
        print(f"  deleted raw_data with operator='tele2': {c.rowcount}")

        if op_id is not None:
            c.execute("DELETE FROM operators WHERE id = ?", (op_id,))
            print(f"  deleted operators row: {c.rowcount}")

        conn.commit()
        print("\nVACUUMing...")
        c.execute("VACUUM")

        # Verify
        print("\n=== Verification ===")
        c.execute("SELECT id, name FROM operators ORDER BY id")
        print("Operators remaining:", c.fetchall())

        c.execute("SELECT operator, COUNT(*) FROM raw_data GROUP BY operator ORDER BY operator")
        print("raw_data by operator:")
        for r in c.fetchall():
            print(" ", r)

        print("\nDone.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()