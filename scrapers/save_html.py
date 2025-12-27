
import requests

url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
resp = requests.get(url, headers=headers)
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)
print("Saved debug_page.html")
