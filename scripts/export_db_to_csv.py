import sqlite3
import csv
import os

def export_db_to_csv(db_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        print(f"Exporting table: {table}...")
        cursor.execute(f"SELECT * FROM {table}")
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        csv_file_path = os.path.join(output_dir, f"{table}.csv")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            writer.writerows(cursor.fetchall())
        print(f"Saved to {csv_file_path}")
    
    conn.close()
    print("Export complete.")

if __name__ == "__main__":
    db_file = 'telecom_outage.db'
    export_folder = 'exports'
    export_db_to_csv(db_file, export_folder)
