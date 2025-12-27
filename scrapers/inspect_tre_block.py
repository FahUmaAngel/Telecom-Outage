
import json

with open('tre_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

try:
    planned = data['props']['pageProps']['page']['blocks'][2]['items'][0]
    print("--- Planned Works Block ---")
    print(json.dumps(planned, indent=2, ensure_ascii=False)[:3000]) # First 3000 chars
except Exception as e:
    print(e)
