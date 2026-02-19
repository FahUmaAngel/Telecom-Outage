import json
import sqlite3

def inspect_raw():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # Check raw_data in raw_outages table if it exists, 
    # but we usually don't keep them long.
    # Let's check if there's any raw data stored.
    try:
        cursor.execute("SELECT raw_data FROM outages WHERE operator_id = (SELECT id FROM operators WHERE name = 'tre') LIMIT 1")
        row = cursor.fetchone()
        if row:
            # Note: The database stores incident details in JSON in columns like title/description,
            # but we might have raw data in a different table or as a blob.
            # In our current setup, we don't store the full raw JSON in the outages table.
            pass
    except:
        pass
    
    conn.close()

if __name__ == "__main__":
    # Instead of DB, let's run the scraper and save results
    from scrapers.tre.fetch import scrape_tre_outages
    raw = scrape_tre_outages()
    if raw:
        with open('tre_raw_sample.json', 'w', encoding='utf-8') as f:
            json.dump(raw[0].raw_data, f, indent=2, ensure_ascii=False)
        print("Saved raw Tre data to tre_raw_sample.json")
    else:
        print("No raw data found")
