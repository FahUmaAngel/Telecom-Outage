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
        match = re.search(r'(\d{1,2})[\.\s]([a-z]{3})\s+(\d{1,2}:\d{2})', date_str)
        if match:
            day, month_abbr, time_part = int(match.group(1)), match.group(2), match.group(3)
            month = months.get(month_abbr)
            if month:
                year = datetime.now().year
                dt_str = f"{year}-{month:02d}-{day:02d} {time_part}"
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except Exception as e:
        print(f"Parse error: {e}")
    return None

def debug_lyca_dates():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    query = """
        SELECT outages.id, outages.incident_id, raw_data.data 
        FROM outages 
        JOIN raw_data ON outages.raw_data_id = raw_data.id 
        WHERE outages.operator_id = (SELECT id FROM operators WHERE name = 'lycamobile') 
        AND outages.end_time IS NULL 
        AND outages.estimated_fix_time IS NULL
        LIMIT 10
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"Checking {len(rows)} incidents from the 'missing' group:")
    for row in rows:
        oid, iid, data_json = row
        data = json.loads(data_json)
        raw = data.get('raw', {})
        
        start_str = raw.get('start_time')
        end_str = raw.get('estimated_end')
        
        parsed_start = parse_swedish_date(start_str)
        parsed_end = parse_swedish_date(end_str)
        
        print(f"ID: {oid} | Incident: {iid}")
        print(f"  Raw Start: {start_str} -> Parsed: {parsed_start}")
        print(f"  Raw End:   {end_str} -> Parsed: {parsed_end}")
        
    conn.close()

if __name__ == "__main__":
    debug_lyca_dates()
