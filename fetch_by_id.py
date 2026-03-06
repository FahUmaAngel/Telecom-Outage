import requests
import json
import time

def fetch_incidents():
    with open("telia_cookies.json", "r") as f:
        cookies_list = json.load(f)
    
    cookies = {c['name']: c['value'] for c in cookies_list}
    
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    base_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/GetFault"
    
    results = {}
    
    for fault_id in target_ids:
        print(f"Fetching {fault_id}...", flush=True)
        try:
            params = {'externalFaultId': fault_id}
            response = requests.get(base_url, params=params, headers=headers, cookies=cookies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    results[fault_id] = data
                    print(f"  Success: {data.get('Title', 'No Title')}")
                else:
                    print(f"  Empty response for {fault_id}")
            else:
                print(f"  Error {response.status_code} for {fault_id}")
        except Exception as e:
            print(f"  Exception for {fault_id}: {e}")
        
        time.sleep(0.5) # Be nice to the server

    with open("fetched_by_id.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Finished. Found {len(results)} out of {len(target_ids)} incidents.")

if __name__ == "__main__":
    fetch_incidents()
