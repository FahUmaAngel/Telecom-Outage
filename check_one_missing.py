# check_one_missing.py
import subprocess
import requests
import json

def refresh_cookies():
    subprocess.run(["python", "get_cookies.py"], check=True)

def fetch_one(incident_id):
    try:
        with open("telia_cookies.json", "r") as f:
            cookies_list = json.load(f)
        cookies = {c['name']: c['value'] for c in cookies_list}
    except FileNotFoundError:
        print("Cookies file not found. Fetching via playwright...")
        refresh_cookies()
        with open("telia_cookies.json", "r") as f:
            cookies_list = json.load(f)
        cookies = {c['name']: c['value'] for c in cookies_list}
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    base_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/GetFault"
    params = {'externalFaultId': incident_id}
    print(f"Fetching {incident_id}...")
    response = requests.get(base_url, params=params, headers=headers, cookies=cookies, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        if not data:
            print("Response is empty []!")

if __name__ == "__main__":
    fetch_one("INCSE0424369")
