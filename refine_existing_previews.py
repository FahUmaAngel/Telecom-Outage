import pandas as pd
import os

def refine_excel(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    print(f"Refining {file_path}...")
    df = pd.read_excel(file_path)

    # 1. Convert duration_hours to numeric for calculation
    # Current values are numbers or "Missing Data"
    df['duration_numeric'] = pd.to_numeric(df['duration_hours'], errors='coerce')

    # 2. Calculate average MTTR per city (location)
    city_averages = df.groupby('location')['duration_numeric'].mean().reset_index()
    city_averages.columns = ['location', 'avg_city_duration_hours']
    city_averages['avg_city_duration_hours'] = city_averages['avg_city_duration_hours'].round(2)

    # 3. Merge averages back to main dataframe
    df = df.merge(city_averages, on='location', how='left')

    # 4. Fill NaN in avg_city_duration_hours (e.g. if all city records are "Missing Data")
    df['avg_city_duration_hours'] = df['avg_city_duration_hours'].fillna("Missing Data")

    # 5. Sort by location (City)
    df = df.sort_values(by=['location', 'start_time'], ascending=[True, False])

    # 6. Reorder columns
    # Re-fetch all columns to preserve metadata, but put key metrics first
    cols = ['location', 'duration_hours', 'avg_city_duration_hours', 'start_time', 'estimated_fix_time', 'title', 'description']
    remaining = [c for c in df.columns if c not in cols and c != 'duration_numeric']
    df = df[cols + remaining]

    # 7. Save back to the same file (or a slightly different one)
    refined_path = file_path.replace('.xlsx', '_refined.xlsx')
    df.to_excel(refined_path, index=False)
    print(f"Done. Refined file saved to: {refined_path}")

if __name__ == "__main__":
    refine_excel("telia_geocoded_full.xlsx")
    refine_excel("lycamobile_geocoded_full.xlsx")
