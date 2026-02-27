import sqlite3
import sys

def find_anomalies(db_path):
    print(f"Checking for time anomalies in: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT o.incident_id, op.name, o.start_time, o.end_time, o.location
            FROM outages o
            JOIN operators op ON o.operator_id = op.id
            WHERE o.end_time < o.start_time
        """
        cursor.execute(query)
        anomalies = cursor.fetchall()
        
        if not anomalies:
            print("No anomalies found (end_time < start_time).")
        else:
            print(f"Found {len(anomalies)} anomalies:")
            for row in anomalies:
                print(f"  ID: {row[0]}, Operator: {row[1]}, Start: {row[2]}, End: {row[3]}, Location: {row[4]}")
                
        # Also check for extremely large durations (potential data entry errors)
        query_large = """
            SELECT o.incident_id, op.name, o.start_time, o.end_time,
                   (julianday(o.end_time) - julianday(o.start_time)) * 24 as hours
            FROM outages o
            JOIN operators op ON o.operator_id = op.id
            WHERE o.end_time >= o.start_time
            ORDER BY hours DESC
            LIMIT 10
        """
        cursor.execute(query_large)
        large_durations = cursor.fetchall()
        print("\nTop 10 longest durations (hours):")
        for row in large_durations:
            print(f"  ID: {row[0]}, Op: {row[1]}, Start: {row[2]}, End: {row[3]}, Hours: {row[4]:.2f}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "telecom_outage.db"
    find_anomalies(db)
