import sqlite3
import pandas as pd

def debug(conn, op_name, op_id):
    df = pd.read_sql_query(f'SELECT * FROM outages WHERE operator_id={op_id}', conn)
    total = len(df)
    
    # Check start_time
    missing_start = df[df['start_time'].isna() | (df['start_time'] == '')]
    m_start_count = len(missing_start)
    
    # Filter to those with start_time for further analysis
    df_s = df[~df.index.isin(missing_start.index)].copy()
    
    # Check end/estimate
    missing_both = df_s[
        (df_s['end_time'].isna() | (df_s['end_time'] == '')) & 
        (df_s['estimated_fix_time'].isna() | (df_s['estimated_fix_time'] == ''))
    ]
    m_both_count = len(missing_both)
    
    # Check locations
    df_valid_times = df_s[~df_s.index.isin(missing_both.index)].copy()
    location_issues = df_valid_times[
        df_valid_times['location'].isna() | 
        df_valid_times['location'].isin(['Unknown', 'Sverige', ''])
    ]
    m_loc_count = len(location_issues)
    
    # Final count (before geocoding)
    final_simple = len(df_valid_times) - m_loc_count
    
    res_s = f"\n--- {op_name} (ID: {op_id}) ---\n"
    res_s += f"Total Records: {total}\n"
    res_s += f"Missing Start Time: {m_start_count}\n"
    res_s += f"Missing Both End/Estimate (but has Start): {m_both_count}\n"
    res_s += f"Generic Location (Unknown/Sverige) after time filter: {m_loc_count}\n"
    res_s += f"Potential Final Count (if no geocoding recovery): {final_simple}\n"
    
    # Duration analysis
    df_valid_times['st'] = pd.to_datetime(df_valid_times['start_time'], errors='coerce')
    df_valid_times['et'] = pd.to_datetime(df_valid_times['end_time'], errors='coerce')
    df_valid_times['eft'] = pd.to_datetime(df_valid_times['estimated_fix_time'], errors='coerce')
    df_valid_times['res'] = df_valid_times['et'].fillna(df_valid_times['eft'])
    
    neg = df_valid_times[df_valid_times['res'] < df_valid_times['st']]
    res_s += f"Negative Durations: {len(neg)}\n"
    if not neg.empty:
        res_s += "Sample Negative Records:\n"
        res_s += neg[['incident_id', 'start_time', 'res', 'location']].head(10).to_string() + "\n"
        
    return res_s

def main():
    conn = sqlite3.connect('telecom_outage.db')
    out = debug(conn, 'telia', 1)
    out += debug(conn, 'lycamobile', 2)
    print(out)
    with open('debug_counts_report.txt', 'w') as f:
        f.write(out)
    conn.close()

if __name__ == "__main__":
    main()
