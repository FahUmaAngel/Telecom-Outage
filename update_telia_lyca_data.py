import sqlite3
import pandas as pd
import os
from datetime import datetime
import requests
import time

# Regions and City Mapping
REGION_MAP = {
    'Stockholms län': 1, 'Västra Götalands län': 2, 'Skåne län': 3,
    'Uppsala län': 4, 'Östergötlands län': 5, 'Jönköpings län': 6,
    'Kronobergs län': 7, 'Kalmar län': 8, 'Gotlands län': 9,
    'Blekinge län': 10, 'Hallands län': 11, 'Värmlands län': 12,
    'Örebro län': 13, 'Västmanlands län': 14, 'Dalarnas län': 15,
    'Gävleborgs län': 16, 'Västernorrlands län': 17, 'Jämtlands län': 18,
    'Västerbottens län': 19, 'Norrbottens län': 20, 'Södermanlands län': 21,
    'Östergötland': 5, 'Södermanland': 21, 'Västmanland': 14, 'Gävleborg': 16
}

CITY_TO_COUNTY = {
    "Stockholm": "Stockholms län", "Göteborg": "Västra Götalands län", "Malmö": "Skåne län",
    "Uppsala": "Uppsala län", "Västerås": "Västmanlands län", "Örebro": "Örebro län",
    "Linköping": "Östergötlands län", "Helsingborg": "Skåne län", "Jönköping": "Jönköpings län",
    "Norrköping": "Östergötlands län", "Lund": "Skåne län", "Umeå": "Västerbottens län",
    "Gävle": "Gävleborgs län", "Borås": "Västra Götalands län", "Södertälje": "Stockholms län",
    "Varberg": "Hallands län", "Eskilstuna": "Södermanlands län", "Falun": "Dalarnas län",
    "Halmstad": "Hallands län", "Karlstad": "Värmlands län", "Växjö": "Kronobergs län",
    "Luleå": "Norrbottens län",
    "Avesta": "Dalarnas län", "Huddinge": "Stockholms län", "Nacka": "Stockholms län",
    "Vaxholm": "Stockholms län", "Vaxholms": "Stockholms län", "Nordanstigs": "Gävleborgs län",
    "Ovanåkers": "Gävleborgs län", "Borgsjö": "Västernorrlands län", "Bollnäs": "Gävleborgs län",
    "Torsby": "Värmlands län", "Tierps": "Uppsala län", "Indals-Liden": "Västernorrlands län",
    "Torp": "Västernorrlands län", "Holm": "Västernorrlands län", "Haverö": "Västernorrlands län",
    "Attmar": "Västernorrlands län"
}

CACHE_GEO = {}

def get_county_from_nominatim(lat, lon):
    if (lat, lon) in CACHE_GEO:
        return CACHE_GEO[(lat, lon)]
    
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
    headers = {'User-Agent': 'TelecomOutageMonitor/1.0'}
    
    try:
        time.sleep(1.2)
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            addr = resp.json().get('address', {})
            county = addr.get('county') or addr.get('state')
            if county:
                for official_county in REGION_MAP.keys():
                    if official_county.lower() in county.lower():
                        CACHE_GEO[(lat, lon)] = official_county
                        return official_county
    except Exception:
        pass
    return None

def normalize_to_lan(row):
    loc_str = str(row['location']) if row['location'] else ''
    lat = row['latitude']
    lon = row['longitude']

    if not loc_str or loc_str in ['Unknown', 'Sverige']:
        if lat and lon:
            return get_county_from_nominatim(lat, lon)
        return None

    for county in REGION_MAP.keys():
        if county.lower() in loc_str.lower():
            return county

    for city, county in CITY_TO_COUNTY.items():
        if city.lower() in loc_str.lower():
            return county

    if lat and lon:
        return get_county_from_nominatim(lat, lon)

    # Final attempt: search for 'län' or specific substrings manually
    l_lower = loc_str.lower()
    for county_name in REGION_MAP.keys():
        nm = county_name.lower().replace(' län', '')
        if nm in l_lower:
            return county_name

    return None

def process_operator(conn, op_name, op_id, min_date=None):
    print(f"\nProcessing {op_name} (ID: {op_id})...")
    df = pd.read_sql_query(f"SELECT * FROM outages WHERE operator_id = {op_id}", conn)
    print(f"  Initial records path count: {len(df)}")

    # YEAR FILTER
    if min_date:
        df['temp_st'] = pd.to_datetime(df['start_time'], errors='coerce', format='mixed', utc=True)
        min_dt = pd.to_datetime(min_date, utc=True)
        df = df[df['temp_st'] >= min_dt]
        print(f"  After year filter ({min_date}): {len(df)}")

    # USE MIXED FORMAT AND UTC TO PREVENT NaT FOR VALID STRINGS
    df['st_dt'] = pd.to_datetime(df['start_time'], errors='coerce', format='mixed', utc=True)
    df['et_dt'] = pd.to_datetime(df['end_time'], errors='coerce', format='mixed', utc=True)
    df['eft_dt'] = pd.to_datetime(df['estimated_fix_time'], errors='coerce', format='mixed', utc=True)

    # Filter: start_time MUST be present
    df = df[df['st_dt'].notna()]
    print(f"  After valid start_time filter: {len(df)}")

    # Filter: either end_time OR estimated_fix_time MUST be present
    df = df[df['et_dt'].notna() | df['eft_dt'].notna()]
    print(f"  After valid end/estimate filter: {len(df)}")

    if df.empty:
        return

    # Calculate MTTR (Duration in Hours)
    # Using UTC timestamps for calculation
    df['resolved_at_dt'] = df['et_dt'].fillna(df['eft_dt'])
    df['duration_hours'] = (df['resolved_at_dt'] - df['st_dt']).dt.total_seconds() / 3600
    df['duration_hours'] = df['duration_hours'].round(2)

    # REMOVE NEGATIVE DURATIONS (likely data errors)
    # Filter out anything less than -0.1 to allow for tiny jitter but remove significant logic errors
    initial_valid_time = len(df)
    df = df[df['duration_hours'] >= 0]
    removed_neg = initial_valid_time - len(df)
    if removed_neg > 0:
        print(f"  Removed {removed_neg} records with negative duration.")

    # Location Mapping
    print("  Updating and mapping locations to Län...")
    df['location_lan'] = df.apply(normalize_to_lan, axis=1)

    # DEBUG: See what we resolved
    if not df.empty:
        print("  DEBUG: Location mapping counts:")
        print(df['location_lan'].value_counts(dropna=False))

    # Filter out unmapped locations
    df = df[df['location_lan'].notna()].copy()
    print(f"  After location resolution/filter: {len(df)}")

    if df.empty:
        return

    # SORT BY LÄN
    df = df.sort_values(by='location_lan').reset_index(drop=True)

    # CALCULATE PER-LÄN MTTR (Average of duration_hours)
    # This will create a column where each row in a Län has the same average value for that Län.
    df['lan_mttr_avg'] = df.groupby('location_lan')['duration_hours'].transform('mean').round(2)

    # Reorder columns for Excel (Column F is index 5)
    cols = [
        'location_lan',      # A
        'duration_hours',    # B
        'start_time',        # C
        'end_time',          # D
        'estimated_fix_time',# E
        'lan_mttr_avg',      # F
        'title',             # G
        'description'        # H
    ]
    remaining = [c for c in df.columns if c not in cols and not c.endswith('_dt') and c != 'resolved_at_dt' and c != 'location']
    
    df_export = df[cols + remaining].copy()
    df_export.rename(columns={'location_lan': 'location', 'lan_mttr_avg': 'MTTR (Län Avg)'}, inplace=True)

    # Clean up dates for Excel (Naive)
    for col in ['start_time', 'end_time', 'estimated_fix_time']:
        dt_col = 'st_dt' if col == 'start_time' else ('et_dt' if col == 'end_time' else 'eft_dt')
        if dt_col in df:
            # We already have aware versions in st_dt, et_dt, eft_dt
            # Convert to naive safely
            df_export[col] = df[dt_col].dt.tz_localize(None)

    # Force string for all other extra columns to prevent openpyxl errors
    for c in remaining:
        df_export[c] = df_export[c].astype(str).replace('nan', '')

    # ADD OVERALL MTTR SUMMARY ROW (SWEDEN)
    overall_mttr = df_export['duration_hours'].mean().round(2)
    # Create empty spacer row
    empty_row = pd.Series([None] * len(df_export.columns), index=df_export.columns)
    # Create summary row
    summary_row = pd.Series([None] * len(df_export.columns), index=df_export.columns)
    summary_row['location'] = 'Sweden'
    summary_row['duration_hours'] = overall_mttr
    
    # Append to export dataframe
    df_export = pd.concat([df_export, empty_row.to_frame().T, summary_row.to_frame().T], ignore_index=True)

    # Save to Excel
    filename = f"{op_name}_geocoded_lan.xlsx"
    print(f"  DEBUG: Final df_export length: {len(df_export)}")
    df_export.to_excel(filename, index=False)
    print(f"  Saved {len(df_export)} records to {filename}")
    
    # Try a unique filename too
    unique_file = f"DEBUG_{op_name}_{int(time.time())}.xlsx"
    df_export.to_excel(unique_file, index=False)
    print(f"  DEBUG: Saved to {unique_file}")

    # Update Database
    cursor = conn.cursor()
    updates = 0
    for idx, row in df.iterrows():
        rid = REGION_MAP.get(row['location_lan'])
        cursor.execute(
            "UPDATE outages SET location = ?, region_id = ? WHERE id = ?",
            (row['location_lan'], rid, row['id'])
        )
        updates += 1
    conn.commit()
    print(f"  Database updated: {updates} records.")

def main():
    db_path = 'telecom_outage.db'
    conn = sqlite3.connect(db_path)
    process_operator(conn, "telia", 1)
    process_operator(conn, "tre", 2, min_date='2026-01-01')
    process_operator(conn, "lycamobile", 3)
    conn.close()
    print("\nProcessing complete.")

if __name__ == "__main__":
    main()
