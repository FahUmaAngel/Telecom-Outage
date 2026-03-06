from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
res = client.get("/api/v1/outages")
print(f"Status: {res.status_code}")
if res.status_code == 200:
    data = res.json()
    tre = [o for o in data if o['operator_name'] == 'Tre']
    print(f"Total out: {len(data)}, Tre out: {len(tre)}")
else:
    print(res.text)
