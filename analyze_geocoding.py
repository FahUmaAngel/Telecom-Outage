import sqlite3

def analyze_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Operators mapping
    cursor.execute("SELECT id, name FROM operators")
    operators = cursor.fetchall()
    
    for op_id, op_name in operators:
        print(f"--- {op_name} (ID {op_id}) ---")
        
        # Total
        cursor.execute("SELECT COUNT(*) FROM outages WHERE operator_id = %s", (op_id,))
        total = cursor.fetchone()[0]
        print(f"Total outages: {total}")
        
        # Has coords but location is Unknown/Empty/Only County
        # For simplicity, let's start with Unknown or Empty
        cursor.execute("""
            SELECT COUNT(*) FROM outages 
            WHERE operator_id = %s
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            AND (location IS NULL OR location = 'Unknown' OR location = '' OR location NOT LIKE '%,%')
        """, (op_id,))
        needs_update = cursor.fetchone()[0]
        print(f"Has coords but potentially missing city: {needs_update}")
        
    conn.close()

if __name__ == "__main__":
    analyze_locations()
