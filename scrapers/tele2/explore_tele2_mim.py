import requests
import json

def test_mim_api():
    print("Testing Tele2 MIM API Endpoint directly...")
    
    url = "https://api-online.tele2.se/mim-api"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-brand': 'tele2',
        'referer': 'https://www.tele2.se/',
        'accept': 'application/json'
    }
    
    # Let's try to get the CSRF/Profile data first, which we saw in the previous log
    print("\n1. GET Request to mim-api")
    try:
        r1 = requests.get(url, headers=headers)
        print(f"Status: {r1.status_code}")
        if r1.status_code == 200:
            print("Response:", json.dumps(r1.json(), indent=2)[:500])
        else:
            print("Response text:", r1.text)
    except Exception as e:
        print(f"Error: {e}")

    # Tele2 might use POST for address lookup
    print("\n2. Trying address lookup via POST (Guessing structure)")
    # A wild guess based on typical graphql or search structures
    ADDRESS = "Drottninggatan 1, Stockholm"
    payloads = [
        {"query": ADDRESS},
        {"address": ADDRESS},
        {"location": {"address": ADDRESS}},
        {"search": ADDRESS}
    ]
    
    for p in payloads:
        print(f"  Testing Payload: {p}")
        try:
            rp = requests.post(url, headers=headers, json=p)
            print(f"  Status: {rp.status_code}")
            if rp.status_code == 200:
                print("  Success! Data:", rp.text[:300])
            else:
                pass # Just ignore errors to keep console clean
        except Exception:
            pass

if __name__ == "__main__":
    test_mim_api()
