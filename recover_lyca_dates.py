import sqlite3
import json
import re
from datetime import datetime, timedelta

def parse_swedish_date(date_str):
    if not date_str: return None
    date_str = date_str.lower().strip()
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'maj': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'dec': 12
    }
    try:
        # Match '18.feb 14:55' or similar
        match = re.search(r'(\d{1,2})[\.\s]([a-z]{3})\s+(\d{1,2}:\d{2})', date_str)
        if match:
            day = int(match.group(1))
            month_abbr = match.group(2)
            time_part = match.group(3)
            month = months.get(month_abbr)
            
            if month:
                now = datetime.now()
                year = now.year
                test_dt = datetime(year, month, day)
                if test_dt > now + timedelta(days=30):
                    year -= 1
                dt_str = f"{year}-{month:02d}-{day:02d} {time_part}"
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except:
        pass
    return None

def recover_lyca_dates():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    # Fetch all Lycamobile outages with missing date info
    query = """
        SELECT outages.id, outages.incident_id, raw_data.data 
        FROM outages 
        JOIN raw_data ON outages.raw_data_id = raw_data.id 
        WHERE outages.operator_id = (SELECT id FROM operators WHERE name = 'lycamobile') 
        AND (outages.start_time IS NULL OR outages.estimated_fix_time IS NULL)
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    updated_count = 0
    not_found_count = 0
    
    for oid, iid, data_json in rows:
        data = json.loads(data_json)
        raw = data.get('raw', {})
        
        raw_start = raw.get('start_time')
        raw_end = raw.get('estimated_end')
        
        parsed_start = parse_swedish_date(raw_start)
        parsed_end = parse_swedish_date(raw_end)
        
        if parsed_start or parsed_end:
            # Update the database
            updates = []
            params = []
            if parsed_start:
                updates.append("start_time = ?")
                params.append(parsed_start.isoformat())
            if parsed_end:
                updates.append("estimated_fix_time = ?")
                params.append(parsed_end.isoformat())
            
            if updates:
                params.append(oid)
                cur.execute(f"UPDATE outages SET {', '.join(updates)} WHERE id = ?", params)
                updated_count += 1
        else:
            not_found_count += 1
            
    conn.commit()
    print(f"Successfully recovered dates for {updated_count} Lycamobile incidents.")
    print(f"Could not find date data in raw_data for {not_found_count} incidents.")
    conn.close()

if __name__ == "__main__":
    recover_lyca_dates()
