import json
import time
from playwright.sync_api import sync_playwright

def fetch_incidents():
    target_ids = [
        "INCSE0504255", "INCSE0500172", "INCSE0508251", "INCSE0504462",
        "INCSE0505843", "INCSE0499021", "INCSE0506219", "INCSE0507801",
        "INCSE0498666", "INCSE0505464", "INCSE0505881", "INCSE0505885",
        "INCSE0505922", "INCSE0506172", "INCSE0502696", "INCSE0502697",
        "INCSE0502694", "INCSE0508167", "INCSE0508249", "INCSE0508259",
        "INCSE0508273", "INCSE0505543", "INCSE0507001", "INCSE0497828",
        "INCSE0505870", "INCSE0505021", "INCSE0497843", "INCSE0508289",
        "INCSE0506784", "INCSE0502566"
    ]
    target_ids = list(set(target_ids))
    
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Opening portal to establish session...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)

        base_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/GetFault"

        for fault_id in target_ids:
            print(f"Fetching {fault_id}...", flush=True)
            try:
                # Use page.evaluate to perform a fetch within the browser context
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
                    results[fault_id] = response_data
                    print(f"  Success: {response_data.get('Title', 'No Title')}")
                else:
                    print(f"  Failed for {fault_id}: {response_data}")
            except Exception as e:
                print(f"  Exception for {fault_id}: {e}")
            
            time.sleep(1)

        browser.close()

    with open("fetched_by_id.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Finished. Found {len(results)} out of {len(target_ids)} incidents.")

if __name__ == "__main__":
    fetch_incidents()
