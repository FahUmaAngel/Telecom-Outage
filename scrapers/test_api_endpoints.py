import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_endpoints():
    endpoints = [
        "/operators",
        "/regions",
        "/reports",
        "/reports/hotspots",
        "/outages",
        "/outages/history"
    ]
    
    for ep in endpoints:
        print(f"Testing {ep}...")
        try:
            resp = requests.get(f"{BASE_URL}{ep}")
            print(f"  Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  Error Response: {resp.text}")
        except Exception as e:
            print(f"  Request failed: {e}")

if __name__ == "__main__":
    test_endpoints()
