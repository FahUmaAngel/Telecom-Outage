import sqlite3
import pandas as pd
import os

def export_db_to_excel():
    db_path = 'telecom_outage.db'
    export_dir = 'exports'
    os.makedirs(export_dir, exist_ok=True)
    excel_path = os.path.join(export_dir, 'telecom_outage_data.xlsx')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    print(f"Found tables: {tables}")
    
    # Create an Excel writer
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for table in tables:
            print(f"Exporting table: {table}")
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            # Write each table to a separate sheet
            df.to_excel(writer, sheet_name=table, index=False)
            print(f"Table '{table}' written with {len(df)} rows.")
            
            # Also save as individual Excel file just in case they want separate files
            individual_excel_path = os.path.join(export_dir, f"{table}.xlsx")
            df.to_excel(individual_excel_path, index=False)
            print(f"Saved separate file: {individual_excel_path}")
            
    conn.close()
    print(f"\n✓ Export complete! All tables exported to multi-sheet workbook: {excel_path}")
    print(f"✓ Individual table Excel files saved in the '{export_dir}' folder.")

if __name__ == '__main__':
    export_db_to_excel()
