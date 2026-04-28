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


def needs_geocode(loc):
    """Check if a location needs geocoding (is a region/county or Unknown)."""
    if not loc: return True
    loc_str = str(loc).lower()
    if loc_str == 'unknown' or loc_str == '' or 'län' in loc_str or ',' not in loc_str:
        return True
    return False

def clean_to_city(loc):
    """Clean location to only show City."""
    if not loc: return "Unknown"
    if ',' in str(loc):
        return str(loc).split(',')[0].strip()
    return str(loc).strip()

def _geocode_row(df, idx, row, updated_count):
    """Attempt geocoding for a single row; fall back to clean_to_city."""
    if pd.notna(row['latitude']) and pd.notna(row['longitude']):
        city = resolve_nominatim(row['latitude'], row['longitude'])
        if city:
            df.at[idx, 'location'] = city
            updated_count += 1
            if updated_count % 5 == 0:
                print(f"  Geocoded {updated_count} records (current: {city})...")
            return updated_count
    df.at[idx, 'location'] = clean_to_city(row['location'])
    return updated_count

def _perform_geocoding(df):
    """Geocode all eligible records in the dataframe."""
    print("Geocoding all eligible records (respecting rate limits)...")
    updated_count = 0
    for idx, row in df.iterrows():
        if needs_geocode(row['location']):
            updated_count = _geocode_row(df, idx, row, updated_count)
        else:
            df.at[idx, 'location'] = clean_to_city(row['location'])
    return updated_count

def _calculate_mttr_metrics(df):
    """Calculate incident duration and city-level MTTR averages based on end_time."""
    def calc_duration(row):
        if pd.isna(row['start_time_dt']) or pd.isna(row['end_time_dt']):
            return "Missing Data"
        dur = (row['end_time_dt'] - row['start_time_dt']).total_seconds() / 3600.0
        # Ignore negative or impossible durations
        if dur <= 0 or dur > 8760:
            return "Invalid Data"
        return round(dur, 2)

    df['duration_hours'] = df.apply(calc_duration, axis=1)
    
    # City-Level MTTR logic
    df['duration_numeric'] = pd.to_numeric(df['duration_hours'], errors='coerce')
    city_avgs = df.groupby('location')['duration_numeric'].mean().reset_index()
    city_avgs.columns = ['location', 'avg_city_duration_hours']
    city_avgs['avg_city_duration_hours'] = city_avgs['avg_city_duration_hours'].round(2)
    
    df = df.merge(city_avgs, on='location', how='left')
    df['avg_city_duration_hours'] = df['avg_city_duration_hours'].fillna("Missing Data")
    return df

def process_operator(op_id, op_name):
    """Main entry point to process an operator's geocoded data."""
    print(f"\n--- Processing {op_name} (ID {op_id}) ---")
    db_path = 'telecom_outage.db'
    if not os.path.exists(db_path):
        db_path = os.path.join('backend', 'telecom_outage.db')
        if not os.path.exists(db_path):
            print("Error: Database not found.")
            return

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM outages WHERE operator_id = {op_id}", conn)
    conn.close()

    if df.empty:
        print(f"No records found for {op_name}.")
        return

    # Date parsing - Use format='mixed' to handle inconsistent T-separator and microseconds
    for col in ['start_time', 'end_time', 'estimated_fix_time']:
        df[f'{col}_dt'] = pd.to_datetime(df[col], errors='coerce', utc=True, format='mixed').dt.tz_localize(None)

    # Ensure non-hashable types (like dicts) are converted to strings for deduplication
    for col in ['title', 'description', 'location']:
        df[col] = df[col].apply(lambda x: str(x) if x is not None else "")

    # Deduplicate - Include end_time for precision
    dedup_cols = ['title', 'description', 'location', 'start_time', 'end_time']
    df = df.drop_duplicates(subset=dedup_cols).copy()
    print(f"Unique incidents to process: {len(df)}")

    # Geocoding
    updated_count = _perform_geocoding(df)

    # MTTR Calculations
    df = _calculate_mttr_metrics(df)
    
    # Final Sorting
    df = df.sort_values(by=['location', 'start_time'], ascending=[True, False])

    # Reorder Columns - Put end_time before estimated_fix_time
    cols = ['location', 'duration_hours', 'avg_city_duration_hours', 'start_time', 'end_time', 'estimated_fix_time', 'title', 'description', 'latitude', 'longitude']
    other_cols = [c for c in df.columns if c not in cols and not c.endswith('_dt') and c != 'duration_numeric']
    df = df[cols + other_cols]
    
    output_file = f"{op_name}_geocoded_full.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Exported {len(df)} records ({updated_count} geocoded) to {output_file}")

if __name__ == "__main__":
    process_operator(1, "telia")
    process_operator(2, "tre")
    process_operator(3, "telenor")
