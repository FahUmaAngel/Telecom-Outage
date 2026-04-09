import sqlite3
import re

def clean_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Clean "Visa område" or " Visa område" from locations
    cursor.execute("SELECT id, location FROM outages WHERE incident_id LIKE 'INCSE%' AND location LIKE '%Visa område%'")
    rows_to_clean = cursor.fetchall()
    
    cleaned_count = 0
    for row in rows_to_clean:
        row_id, location = row
        if not location: continue
        
        # Remove the exact phrase, perhaps with a leading space
        new_location = re.sub(r'\s*Visa område\s*', '', location).strip()
        
        # If the string was *only* "Visa område", it will now be empty. Handled below or keep as empty string.
        cursor.execute("UPDATE outages SET location = ? WHERE id = ?", (new_location, row_id))
        cleaned_count += 1
        
    conn.commit()
    print("--------------------------------------------------")
    print(f"Removed 'Visa område' from {cleaned_count} incident locations.")
    print("--------------------------------------------------")
    
    # 2. Find all incidents where location is empty, null, or literally "Unknown"
    cursor.execute("""
        SELECT incident_id, location 
        FROM outages 
        WHERE incident_id LIKE 'INCSE%' 
        AND (location IS NULL OR location = '' OR location LIKE '%unknown%' COLLATE NOCASE)
    """)
    unknown_rows = cursor.fetchall()
    
    print(f"Total INCSE incidents with Unknown/Empty location: {len(unknown_rows)}")
    print("--------------------------------------------------")
    for row in unknown_rows:
        incident_id, loc = row
        # print just the ID, loc is empty/unknown anyway
        print(f"{incident_id} (Location field: '{loc}')")
        
    conn.close()

if __name__ == "__main__":
    clean_locations()
