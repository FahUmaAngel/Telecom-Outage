import requests

res = requests.get("http://localhost:8001/api/v1/outages").json()
tre_outages = [o for o in res if str(o.get('operator_name', '')).lower() == 'tre']

print(f"Total Tre outages in unfiltered API: {len(tre_outages)}")
for o in tre_outages[:10]:
    print(f"Title: {o['title']['sv']}")
    print(f"  Start: {o['start_time']}")
    print(f"  End:   {o['end_time']}")
    print(f"  Target:{o['estimated_fix_time']}\n")
