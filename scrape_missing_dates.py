import json
import time
import sqlite3
from playwright.sync_api import sync_playwright

def scrape_missing_dates():
    # 1. Get the 317 IDs from the database
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    cursor.execute("SELECT incident_id FROM outages WHERE end_time IS NULL AND incident_id LIKE 'INCSE%'")
    rows = cursor.fetchall()
    conn.close()
    
    target_ids = [r[0] for r in rows]
    print(f"Loaded {len(target_ids)} INCSE IDs to scrape for end dates.")
    
    results = {}
    base_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/GetFault"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Opening portal to establish session...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)

        for i, fault_id in enumerate(target_ids):
            print(f"[{i+1}/{len(target_ids)}] Fetching {fault_id}...", flush=True)
            try:
                response_data = page.evaluate(f"""
                    async () => {{
                        const res = await fetch("{base_url}?externalFaultId={fault_id}", {{
                            headers: {{ 'X-Requested-With': 'XMLHttpRequest' }}
                        }});
                        if (res.ok) {{
                            const text = await res.text();
                            try {{
                                return JSON.parse(text);
                            }} catch (e) {{
                                return {{ error: "not_json", body: text }};
                            }}
                        }}
                        return {{ error: "http_error", status: res.status }};
                    }}
                """)
                
                if response_data and "error" not in response_data:
                    # We only care about saving it if it actually has an EndTime
                    if response_data.get('EndTime'):
                        results[fault_id] = response_data['EndTime']
                        print(f"  Success: EndTime found -> {response_data['EndTime']}")
                    else:
                        print(f"  Data retrieved, but no EndTime present.")
                else:
                    print(f"  Failed for {fault_id}: {response_data}")
            except Exception as e:
                print(f"  Exception for {fault_id}: {e}")
            
            # Save progress periodically
            if (i + 1) % 10 == 0:
                with open("recovered_end_dates.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                print(f"--- Saved progress ({len(results)} found so far) ---")
            
            # Sleep to avoid rate limiting
            time.sleep(0.5)

        browser.close()

    # Final save
    with open("recovered_end_dates.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nFinished scraping. Recovered {len(results)} end dates out of {len(target_ids)} attempts.")

if __name__ == "__main__":
    scrape_missing_dates()
