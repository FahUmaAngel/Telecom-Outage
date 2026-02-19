import requests
import json

try:
    response = requests.get("http://localhost:8000/api/v1/outages")
    if response.status_code == 200:
        data = response.json()
        results = {
            "total": len(data),
            "null_start_time_ids": [o['id'] for o in data if o.get('start_time') is None],
            "sample": data[0] if data else None
        }
        with open("api_dates_debug.json", "w") as f:
            json.dump(results, f, indent=2)
        print("Results saved to api_dates_debug.json")
    else:
        print(f"API Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
