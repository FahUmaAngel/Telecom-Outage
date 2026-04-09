import sqlite3
import json
import re
import time
from playwright.sync_api import sync_playwright

def extract_location_from_text(sv_text):
    # Common pattern in Telia data: "Planerat arbete i [City]" or "Driftstörning i [City]"
    if not sv_text: return None
    
    # Try finding "arbete i " followed by word(s)
    match = re.search(r'arbete i ([A-ZÅÄÖa-zåäö\s\,]+)(?=\b|$)', sv_text)
    if match:
        return match.group(1).strip()
        
    match = re.search(r'störning i ([A-ZÅÄÖa-zåäö\s\,]+)(?=\b|$)', sv_text)
    if match:
        return match.group(1).strip()
        
    return None

def scrape_missing_locations():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Get the empty/Unknown locations
    cursor.execute("""
        SELECT id, incident_id, title, description 
        FROM outages 
        WHERE incident_id LIKE 'INCSE%' 
        AND (location IS NULL OR location = '' OR location LIKE '%unknown%' COLLATE NOCASE)
    """)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} INCSE incidents with Unknown locations to recover.")
    
    base_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/GetFault"
    updates_made = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Opening portal to establish session...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)

        for i, row in enumerate(rows):
            row_id, fault_id, title_json, desc_json = row
            found_location = None
            
            print(f"[{i+1}/{len(rows)}] Processing {fault_id}...", flush=True)
            
            # METHOD 1: Try scraping the API directly for Municipality/City
            try:
                response_data = page.evaluate(f"""
                    async () => {{
                        const res = await fetch("{base_url}?externalFaultId={fault_id}", {{
                            headers: {{ 'X-Requested-With': 'XMLHttpRequest' }}
                        }});
                        if (res.ok) {{
                            const text = await res.text();
                            try {{ return JSON.parse(text); }} 
                            catch (e) {{ return {{ error: "not_json" }}; }}
                        }}
                        return {{ error: "http_error", status: res.status }};
                    }}
                """)
                
                if response_data and "error" not in response_data:
                    city = response_data.get('City')
                    municipality = response_data.get('MunicipalityName')
                    # Prefer Municipality if available, else City
                    found_location = municipality if municipality else city
                    if found_location:
                        print(f"  -> Found via API: {found_location}")
            except Exception as e:
                print(f"  API Error: {e}")
            
            # METHOD 2: Fallback to text analysis of local DB title and description
            if not found_location:
                try:
                    title_dict = json.loads(title_json) if title_json else {}
                    desc_dict = json.loads(desc_json) if desc_json else {}
                    
                    sv_text = title_dict.get('sv', '') + " " + desc_dict.get('sv', '')
                    
                    extracted = extract_location_from_text(sv_text)
                    if extracted:
                        found_location = extracted
                        print(f"  -> Found via Text Analysis: {found_location}")
                except Exception as e:
                    pass
            
            # Apply update to Database
            if found_location:
                cursor.execute("UPDATE outages SET location = ? WHERE id = ?", (found_location, row_id))
                updates_made += 1
            else:
                # Set explicitly to "Unknown" instead of "Unknown, Unknown" or empty
                cursor.execute("UPDATE outages SET location = 'Unknown' WHERE id = ?", (row_id,))
                
            # Sleep to avoid rate limiting
            time.sleep(0.3)

        browser.close()

    conn.commit()
    conn.close()
    
    print(f"\nFinished. Updated {updates_made} incidents with recovered locations.")

if __name__ == "__main__":
    scrape_missing_locations()
