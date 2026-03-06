import json
import time
import sqlite3
from playwright.sync_api import sync_playwright

def scrape_missing_dates_html():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    cursor.execute("SELECT incident_id FROM outages WHERE end_time IS NULL AND incident_id LIKE 'INCSE%'")
    rows = cursor.fetchall()
    conn.close()
    
    target_ids = [r[0] for r in rows]
    print(f"Loaded {len(target_ids)} INCSE IDs to scrape via HTML DOM.")
    
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Opening portal...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)

        for i, fault_id in enumerate(target_ids):
            print(f"[{i+1}/{len(target_ids)}] Scraping {fault_id}...", flush=True)
            try:
                # Type into search box and hit enter to load the fault
                page.fill('#searchBox', fault_id)
                page.press('#searchBox', 'Enter')
                
                # Wait a moment for UI to update (might not exist)
                page.wait_for_timeout(2000)
                
                # Try to extract the date specifically from the UI card if it pops up
                end_date = page.evaluate("""
                    () => {
                        // The Telia portal usually shows dates in elements with classes like .timeLabel or specific dt/dd pairs
                        // Look for the "Beräknas klart" or "Ends" equivalent text
                        let cards = document.querySelectorAll('.card-content, .info-window');
                        for(let c of cards) {
                             if(c.textContent.includes('INCSE')) {
                                  // Simplified extraction, this needs to be tuned to the actual UI
                                  return c.innerText; 
                             }
                        }
                        return null;
                    }
                """)
                
                if end_date:
                    results[fault_id] = end_date
                    print(f"  Found data blocks for {fault_id}")
                else:
                    print(f"  No card appeared for {fault_id}")
                    
                # Clear search for next
                page.fill('#searchBox', '')
                
            except Exception as e:
                print(f"  Exception for {fault_id}: {e}")
            
            if (i + 1) % 5 == 0:
                with open("html_recovered_dates.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
            
        browser.close()

if __name__ == "__main__":
    scrape_missing_dates_html()
