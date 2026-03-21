import sqlite3
import json

def analyze_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Operators mapping
    cursor.execute("SELECT id, name FROM operators")
    operators = cursor.fetchall()
    
    analysis = {}
    for op_id, op_name in operators:
        # Total
        cursor.execute(f"SELECT COUNT(*) FROM outages WHERE operator_id = {op_id}")
        total = cursor.fetchone()[0]
        
        # Missing City (location is NULL, Empty, Unknown, or just shows a County ' län')
        cursor.execute(f"""
            SELECT COUNT(*) FROM outages 
            WHERE operator_id = {op_id}
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            AND (location IS NULL OR location = 'Unknown' OR location = '' OR location NOT LIKE '%,%')
        """)
        needs_update = cursor.fetchone()[0]
        
        analysis[op_name] = {
            "total": total,
            "needs_update": needs_update
        }
        
    conn.close()
    with open('geocoding_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=4)
        
if __name__ == "__main__":
    analyze_locations()
