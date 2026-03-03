import requests
import re
import urllib.parse

def test_admin_area_api():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
    })
    
    # 1. Get the page and extract the token
    url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
    r = s.get(url)
    
    match = re.search(r'<input type="hidden" value="([^"]+)" id="csrft"', r.text)
    if not match:
        print("Could not find csrft token!")
        return
        
    token = match.group(1)
    
    # 2. Call AdminAreaList exactly as the browser does it
    api_url = f"https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/AdminAreaList?&ert={token}"
    
    print(f"Calling {api_url}")
    
    r_api = s.get(api_url)  # Let it use the raw URL
    print(f"Status Code: {r_api.status_code}")
    
    if r_api.status_code == 200:
        try:
            data = r_api.json()
            print(f"Success! Retrieved {len(data)} admin areas.")
            for area in data[:3]:
                print(f" - {area.get('Name')}")
        except Exception as e:
            print(f"Failed to parse JSON. Response preview:\n{r_api.text[:300]}")
    else:
        print(f"Failed. Response preview:\n{r_api.text[:300]}")

if __name__ == "__main__":
    test_admin_area_api()
