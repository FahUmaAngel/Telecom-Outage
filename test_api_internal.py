import requests
import json

def test_api():
    base_url = "http://127.0.0.1:8001/api/v1"
    try:
        response = requests.get(f"{base_url}/outages/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data)} outages via API.")
            if data:
                print("First outage sample:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    test_api()
