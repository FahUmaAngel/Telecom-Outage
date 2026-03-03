import requests
import re
import urllib.parse

def test_admin_area_api():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    # 1. Get the page and extract the token
    url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
    print(f"Loading {url}...")
    r = s.get(url)
    
    match = re.search(r'<input type="hidden" value="([^"]+)" id="csrft"', r.text)
    if not match:
        print("Could not find csrft token!")
        return
        
    token = match.group(1)
    # The token in the HTML is already URL-encoded (e.g. %2b, %3d).
    # When we pass it in requests.get(params=...), requests will URL-encode it AGAIN.
    # So we must unquote it first to get the raw base64-like string.
    raw_token = urllib.parse.unquote(token)
    
    print(f"Extracted Raw Token: {raw_token[:30]}...")
    
    # 2. Call AdminAreaList
    api_url = "https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/AdminAreaList"
    params = {'ert': raw_token}
    
    print(f"Calling {api_url} with ert parameter...")
    # Add a referer and X-Requested-With just in case it's checking headers
    headers = {
        "Referer": url,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    
    r_api = s.get(api_url, params=params, headers=headers)
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
