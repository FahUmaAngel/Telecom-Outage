import pandas as pd
import sqlite3
import requests
import time
import os

def resolve_nominatim(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    # zoom=14 for better city/town resolution
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 14, 'addressdetails': 1}
    headers = {'User-Agent': 'TelecomOutageMonitor/1.0 (Full Geocoding)'}
    try:
        time.sleep(1.1)
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            addr = resp.json().get('address', {})
            # Improved specificity priority
            city = addr.get('city') or addr.get('town') or addr.get('village') or \
                   addr.get('hamlet') or addr.get('suburb') or addr.get('municipality')
            if city:
                if ' kommun' in city:
                    city = city.replace(' kommun', '')
                return city
    except Exception as e:
        print(f"Error during geocoding: {e}")
    return None

def process_operator(op_id, op_name):
    print(f"\n--- Processing {op_name} (ID {op_id}) ---")
    db_path = 'telecom_outage.db'
    if not os.path.exists(db_path):
        db_path = os.path.join('backend', 'telecom_outage.db')
        if not os.path.exists(db_path):
            print("Error: Database not found.")
            return

    conn = sqlite3.connect(db_path)
    # Include ALL records for the operator to show data gaps clearly
    query = f"SELECT * FROM outages WHERE operator_id = {op_id}"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print(f"No records found for {op_name}.")
        return

    # Robust date parsing
    try:
        df['start_time_dt'] = pd.to_datetime(df['start_time'], utc=True).dt.tz_localize(None)
        df['estimated_fix_time_dt'] = pd.to_datetime(df['estimated_fix_time'], utc=True).dt.tz_localize(None)
    except:
        df['start_time_dt'] = pd.to_datetime(df['start_time'], errors='coerce', utc=True).dt.tz_localize(None)
        df['estimated_fix_time_dt'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce', utc=True).dt.tz_localize(None)

    # Deduplicate
    dedup_cols = ['title', 'description', 'location', 'start_time', 'estimated_fix_time']
    df = df.drop_duplicates(subset=dedup_cols).copy()
    print(f"Unique incidents to process: {len(df)}")

    # Calculate MTTR
    def calc_duration(row):
        if pd.isna(row['start_time_dt']) or pd.isna(row['estimated_fix_time_dt']):
            return "Missing Data"
        dur = (row['estimated_fix_time_dt'] - row['start_time_dt']).total_seconds() / 3600.0
        return round(dur, 2)

    df['duration_hours'] = df.apply(calc_duration, axis=1)

    # Function to check if a location needs geocoding (is a region/county or Unknown)
    def needs_geocode(loc):
        if not loc: return True
        loc_str = str(loc).lower()
        if loc_str == 'unknown' or loc_str == '' or 'län' in loc_str or ',' not in loc_str:
            return True
        return False

    # Function to clean location to only show City
    def clean_to_city(loc):
        if not loc: return "Unknown"
        if ',' in str(loc):
            return str(loc).split(',')[0].strip()
        return str(loc).strip()

    print("Geocoding all eligible records (respecting rate limits)...")
    updated_count = 0
    
    for idx, row in df.iterrows():
        if needs_geocode(row['location']):
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                city = resolve_nominatim(row['latitude'], row['longitude'])
                if city:
                    df.at[idx, 'location'] = city
                    updated_count += 1
                    if updated_count % 10 == 0:
                        print(f"  Geocoded {updated_count} records...")
                else:
                    df.at[idx, 'location'] = clean_to_city(row['location'])
            else:
                df.at[idx, 'location'] = clean_to_city(row['location'])
        else:
            df.at[idx, 'location'] = clean_to_city(row['location'])

    output_file = f"{op_name}_geocoded_full.xlsx"
    
    # NEW: Sorting and City-Level MTTR logic
    # 1. Convert duration_hours to numeric for aggregation
    df['duration_numeric'] = pd.to_numeric(df['duration_hours'], errors='coerce')
    
    # 2. Calculate average MTTR per city
    city_avgs = df.groupby('location')['duration_numeric'].mean().reset_index()
    city_avgs.columns = ['location', 'avg_city_duration_hours']
    city_avgs['avg_city_duration_hours'] = city_avgs['avg_city_duration_hours'].round(2)
    
    # 3. Merge back
    df = df.merge(city_avgs, on='location', how='left')
    df['avg_city_duration_hours'] = df['avg_city_duration_hours'].fillna("Missing Data")
    
    # 4. Sort by location and then start_time
    df = df.sort_values(by=['location', 'start_time'], ascending=[True, False])

    # Reorder columns
    cols = ['location', 'duration_hours', 'avg_city_duration_hours', 'start_time', 'estimated_fix_time', 'title', 'description', 'latitude', 'longitude']
    other_cols = [c for c in df.columns if c not in cols and not c.endswith('_dt') and c != 'duration_numeric']
    df = df[cols + other_cols]
    
    df.to_excel(output_file, index=False)
    print(f"Exported {len(df)} records ({updated_count} geocoded) to {output_file}")

if __name__ == "__main__":
    process_operator(1, "telia")
    process_operator(3, "lycamobile")
