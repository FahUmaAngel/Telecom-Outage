import requests
from bs4 import BeautifulSoup
import json

TRE_URL = "https://www.tre.se/varfor-tre/tackning/driftstorningar"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_and_save():
    print(f"Fetching {TRE_URL}...")
    response = requests.get(TRE_URL, headers=HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data = soup.find('script', id='__NEXT_DATA__')
        
        if next_data:
            print("Found __NEXT_DATA__, saving to scrapers/tre_debug.json")
            data = json.loads(next_data.string)
            with open('scrapers/tre_debug.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            print("No __NEXT_DATA__ found.")
    else:
        print(f"Failed to fetch: {response.status_code}")

if __name__ == "__main__":
    fetch_and_save()
