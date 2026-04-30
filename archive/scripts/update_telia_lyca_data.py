import sqlite3
import pandas as pd
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

_STOCKHOLM = "Stockholms län"
_SKANE = "Skåne län"
_VASTERNORRLAND = "Västernorrlands län"
_GAVLEBORG = "Gävleborgs län"
_VASTGOTA = "Västra Götalands län"
_OSTERGOTLAND = "Östergötlands län"

CITY_TO_COUNTY = {
    "Stockholm": _STOCKHOLM, "Göteborg": _VASTGOTA, "Malmö": _SKANE,
    "Uppsala": "Uppsala län", "Västerås": "Västmanlands län", "Örebro": "Örebro län",
    "Linköping": _OSTERGOTLAND, "Helsingborg": _SKANE, "Jönköping": "Jönköpings län",
    "Norrköping": _OSTERGOTLAND, "Lund": _SKANE, "Umeå": "Västerbottens län",
    "Gävle": _GAVLEBORG, "Borås": _VASTGOTA, "Södertälje": _STOCKHOLM,
    "Varberg": "Hallands län", "Eskilstuna": "Södermanlands län", "Falun": "Dalarnas län",
    "Halmstad": "Hallands län", "Karlstad": "Värmlands län", "Växjö": "Kronobergs län",
    "Luleå": "Norrbottens län",
    "Avesta": "Dalarnas län", "Huddinge": _STOCKHOLM, "Nacka": _STOCKHOLM,
    "Vaxholm": _STOCKHOLM, "Vaxholms": _STOCKHOLM, "Nordanstigs": _GAVLEBORG,
    "Ovanåkers": _GAVLEBORG, "Borgsjö": _VASTERNORRLAND, "Bollnäs": _GAVLEBORG,
    "Torsby": "Värmlands län", "Tierps": "Uppsala län", "Indals-Liden": _VASTERNORRLAND,
    "Torp": _VASTERNORRLAND, "Holm": _VASTERNORRLAND, "Haverö": _VASTERNORRLAND,
    "Attmar": _VASTERNORRLAND,
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

def _match_county_by_name(loc_lower: str):
    for county in REGION_MAP:
        if county.lower() in loc_lower:
            return county
    return None

def _match_county_by_city(loc_lower: str):
    for city, county in CITY_TO_COUNTY.items():
        if city.lower() in loc_lower:
            return county
    return None

def _match_county_partial(loc_lower: str):
    for county_name in REGION_MAP:
        if county_name.lower().replace(' län', '') in loc_lower:
            return county_name
    return None

def normalize_to_lan(row):
    loc_str = str(row['location']) if row['location'] else ''
    lat, lon = row['latitude'], row['longitude']

    if not loc_str or loc_str in ['Unknown', 'Sverige']:
        return get_county_from_nominatim(lat, lon) if (lat and lon) else None

    loc_lower = loc_str.lower()
    return (
        _match_county_by_name(loc_lower)
        or _match_county_by_city(loc_lower)
        or (get_county_from_nominatim(lat, lon) if (lat and lon) else None)
        or _match_county_partial(loc_lower)
    )

_COL_DT_MAP = {'start_time': 'st_dt', 'end_time': 'et_dt', 'estimated_fix_time': 'eft_dt'}

def _prepare_timestamps(df):
    for col, dt_col in _COL_DT_MAP.items():
        df[dt_col] = pd.to_datetime(df[col], errors='coerce', format='mixed', utc=True)
    return df

def _filter_valid_records(df):
    df = df[df['st_dt'].notna()]
    print(f"  After valid start_time filter: {len(df)}")
    df = df[df['et_dt'].notna() | df['eft_dt'].notna()]
    print(f"  After valid end/estimate filter: {len(df)}")
    return df

def _calculate_durations(df):
    df['resolved_at_dt'] = df['et_dt'].fillna(df['eft_dt'])
    df['duration_hours'] = (df['resolved_at_dt'] - df['st_dt']).dt.total_seconds() / 3600
    df['duration_hours'] = df['duration_hours'].round(2)
    initial = len(df)
    df = df[df['duration_hours'] >= 0]
    removed = initial - len(df)
    if removed > 0:
        print(f"  Removed {removed} records with negative duration.")
    return df

def _build_export_df(df):
    df['lan_mttr_avg'] = df.groupby('location_lan')['duration_hours'].transform('mean').round(2)
    cols = ['location_lan', 'duration_hours', 'start_time', 'end_time', 'estimated_fix_time', 'lan_mttr_avg', 'title', 'description']
    remaining = [c for c in df.columns if c not in cols and not c.endswith('_dt') and c != 'resolved_at_dt' and c != 'location']
    df_export = df[cols + remaining].copy()
    df_export.rename(columns={'location_lan': 'location', 'lan_mttr_avg': 'MTTR (Län Avg)'}, inplace=True)
    for col, dt_col in _COL_DT_MAP.items():
        if dt_col in df:
            df_export[col] = df[dt_col].dt.tz_localize(None)
    for c in remaining:
        df_export[c] = df_export[c].astype(str).replace('nan', '')
    overall_mttr = df_export['duration_hours'].mean().round(2)
    empty_row = pd.Series([None] * len(df_export.columns), index=df_export.columns)
    summary_row = pd.Series([None] * len(df_export.columns), index=df_export.columns)
    summary_row['location'] = 'Sweden'
    summary_row['duration_hours'] = overall_mttr
    return pd.concat([df_export, empty_row.to_frame().T, summary_row.to_frame().T], ignore_index=True)

def _update_database(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        rid = REGION_MAP.get(row['location_lan'])
        cursor.execute(
            "UPDATE outages SET location = ?, region_id = ? WHERE id = ?",
            (row['location_lan'], rid, row['id'])
        )
    conn.commit()
    print(f"  Database updated: {len(df)} records.")

def process_operator(conn, op_name, op_id, min_date=None):
    print(f"\nProcessing {op_name} (ID: {op_id})...")
    df = pd.read_sql_query(f"SELECT * FROM outages WHERE operator_id = {op_id}", conn)
    print(f"  Initial records: {len(df)}")

    if min_date:
        df['temp_st'] = pd.to_datetime(df['start_time'], errors='coerce', format='mixed', utc=True)
        df = df[df['temp_st'] >= pd.to_datetime(min_date, utc=True)]
        print(f"  After year filter ({min_date}): {len(df)}")

    df = _prepare_timestamps(df)
    df = _filter_valid_records(df)
    if df.empty:
        return

    df = _calculate_durations(df)

    print("  Updating and mapping locations to Län...")
    df['location_lan'] = df.apply(normalize_to_lan, axis=1)
    print(df['location_lan'].value_counts(dropna=False))

    df = df[df['location_lan'].notna()].copy()
    print(f"  After location resolution/filter: {len(df)}")
    if df.empty:
        return

    df = df.sort_values(by='location_lan').reset_index(drop=True)
    df_export = _build_export_df(df)

    filename = f"{op_name}_geocoded_lan.xlsx"
    df_export.to_excel(filename, index=False)
    print(f"  Saved {len(df_export)} records to {filename}")

    unique_file = f"DEBUG_{op_name}_{int(time.time())}.xlsx"
    df_export.to_excel(unique_file, index=False)
    print(f"  DEBUG: Saved to {unique_file}")

    _update_database(conn, df)

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
