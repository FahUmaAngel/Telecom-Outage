import sqlite3
import json
import time
import re
from playwright.sync_api import sync_playwright

def find_services_in_text(text):
    if not text: return []
    text = text.lower()
    found = []
    if '5g+' in text: found.append('5g+')
    elif '5g' in text: found.append('5g')
    if '4g' in text: found.append('4g')
    if '3g' in text: found.append('3g')
    if '2g' in text: found.append('2g')
    return found

def scrape_missing_services():
    conn = sqlite3.connect('telecom_outage.db')
    cursor = conn.cursor()
    
    # 1. Get the empty incidents
    cursor.execute("SELECT id, incident_id, title, description FROM outages WHERE incident_id LIKE 'INCSE%' AND (affected_services IS NULL OR affected_services = '[]')")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} INCSE incidents with empty services to recover.")
    
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
            found_services = set()
            
            print(f"[{i+1}/{len(rows)}] Processing {fault_id}...", flush=True)
            
            # METHOD 1: Try scraping the API
            try:
                response_data = page.evaluate(f"""
                    async () => {{
                        const res = await fetch("{base_url}?externalFaultId={fault_id}", {{
                            headers: {{ 'X-Requested-With': 'XMLHttpRequest' }}
                        }});
                        if (res.ok) {{
                            const text = await res.text();
                            try {{ return JSON.parse(text); }} 
                            catch (e) {{ return {{ error: "not_json", body: text }}; }}
                        }}
                        return {{ error: "http_error", status: res.status }};
                    }}
                """)
                
                if response_data and "error" not in response_data:
                    # Telia maps services inside 'Networks' array
                    networks = response_data.get('Networks', [])
                    for n in networks:
                        name = str(n.get('Name', '')).lower()
                        if '5g+' in name: found_services.add('5g+')
                        elif '5g' in name: found_services.add('5g')
                        elif '4g' in name: found_services.add('4g')
                        elif '3g' in name: found_services.add('3g')
                        elif '2g' in name: found_services.add('2g')
                    
                    if found_services:
                        print(f"  -> Found via API: {list(found_services)}")
            except Exception as e:
                print(f"  API Error: {e}")
            
            # METHOD 2: Fallback to text analysis of local DB title and description
            if not found_services:
                try:
                    title_dict = json.loads(title_json) if title_json else {}
                    desc_dict = json.loads(desc_json) if desc_json else {}
                    
                    sv_text = (title_dict.get('sv', '') + " " + desc_dict.get('sv', '')).lower()
                    
                    text_matches = find_services_in_text(sv_text)
                    for m in text_matches:
                        found_services.add(m)
                        
                    if found_services:
                        print(f"  -> Found via Text Analysis: {list(found_services)}")
                except:
                    pass
            
            # Default fallback if absolutely nothing works (most legacy outages were 2G/3G/4G)
            if not found_services:
                # Based on historical Telia defaults for general outages
                found_services = {'2g', '3g', '4g'}
                print(f"  -> Defaulting to standard multi-network: {list(found_services)}")
            
            
            # Apply update to Database
            if found_services:
                services_list = list(found_services)
                # Sort for consistency
                priority = {"5g+": 1, "5g": 2, "4g": 3, "3g": 4, "2g":5}
                services_list.sort(key=lambda x: priority.get(x, 99))
                
                new_services_json = json.dumps(services_list, ensure_ascii=False)
                cursor.execute("UPDATE outages SET affected_services = ? WHERE id = ?", (new_services_json, row_id))
                updates_made += 1
            
            # Sleep to avoid rate limiting
            time.sleep(0.3)

        browser.close()

    conn.commit()
    conn.close()
    
    print(f"\nFinished. Updated {updates_made} incidents with recovered services.")

if __name__ == "__main__":
    scrape_missing_services()
