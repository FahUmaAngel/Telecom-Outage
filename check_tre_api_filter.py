import requests
import json

try:
    res = requests.get("http://localhost:8001/api/v1/outages?operator=tre")
    print(f"Status CODE: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Total matching: {len(data)}")
        if data:
            print(json.dumps(data[0], indent=2))
    else:
        print(res.text)
except Exception as e:
    print(f"Error: {e}")
