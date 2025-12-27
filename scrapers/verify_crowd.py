"""
Verification script for Crowd Detection.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_hotspots():
    print("--- Testing Hotspots API ---")
    
    # 1. Check initial hotspots (should have external signals from mock)
    print("Fetching initial hotspots...")
    resp = requests.get(f"{BASE_URL}/reports/hotspots")
    print(f"Status: {resp.status_code}")
    print(f"Data: {json.dumps(resp.json(), indent=2)}")
    
    # 2. Seed User Reports in Stockholms län (id=1 usually)
    print("\nSeeding 6 reports in Stockholm (Threshold is 5)...")
    for i in range(6):
        data = {
            "operator_name": "telia",
            "title": f"No signal in Stockholm {i}",
            "description": "Nothing works",
            "latitude": 59.3293,
            "longitude": 18.0686
        }
        requests.post(f"{BASE_URL}/reports/", json=data)
        
    # 3. Check hotspots again
    print("\nFetching hotspots after seeding...")
    resp = requests.get(f"{BASE_URL}/reports/hotspots")
    hotspots = resp.json()
    print(f"Data: {json.dumps(hotspots, indent=2)}")
    
    # Verify we found a USER_CLUSTER
    user_clusters = [h for h in hotspots if h["type"] == "USER_CLUSTER"]
    if user_clusters:
        print("\n✅ SUCCESS: User cluster detected!")
    else:
        print("\n❌ FAILURE: User cluster not detected.")

if __name__ == "__main__":
    test_hotspots()
