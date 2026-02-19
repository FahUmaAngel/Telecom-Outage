import requests
import json

try:
    response = requests.get("http://localhost:8000/api/v1/outages")
    if response.status_code == 200:
        data = response.json()
        print(f"Total outages: {len(data)}")
        
        # Check for null start_time
        null_starts = [o['id'] for o in data if o.get('start_time') is None]
        print(f"Records with null start_time: {null_starts}")
        
        if data:
            print("\nSample record:")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"API returned status {response.status_code}")
except Exception as e:
    print(f"Error fetching API: {e}")

try:
    response = requests.get("http://localhost:8000/api/v1/reports") # Assuming this is user reports
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal reports: {len(data)}")
        null_created = [r['id'] for r in data if r.get('created_at') is None]
        print(f"Reports with null created_at: {null_created}")
        if data:
            print("\nSample report:")
            print(json.dumps(data[0], indent=2))
except Exception as e:
    print(f"Error fetching reports API: {e}")
