import requests
from bs4 import BeautifulSoup
import json

url = "https://www.tre.se/varfor-tre/tackning/driftstorningar"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')
next_data = soup.find('script', id='__NEXT_DATA__')
if next_data:
    data = json.loads(next_data.string)
    with open('tre_next_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Dumped __NEXT_DATA__ to tre_next_data.json")
else:
    print("No __NEXT_DATA__ found")
