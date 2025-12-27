
import requests
import re
import logging

logging.basicConfig(level=logging.INFO)

url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Length: {len(resp.text)}")

# Simple search
if 'ert' in resp.text:
    print("Found 'ert' in text!")
    # Show context
    start = resp.text.find('ert')
    print(f"Context: {resp.text[start:start+100]}")
else:
    print("'ert' not found in text.")

# Check cookies
print("Cookies:", resp.cookies.get_dict())
