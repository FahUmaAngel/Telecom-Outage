
import json

with open('tre_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def search_json(obj, term, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                search_json(v, term, path + f".{k}")
            elif isinstance(v, str) and term.lower() in v.lower():
                print(f"Found '{term}' at {path}.{k}: {v[:100]}...")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            search_json(item, term, path + f"[{i}]")

print("Searching for 'Planerade'...")
search_json(data, "Planerade")
print("\nSearching for 'Störning'...")
search_json(data, "Störning")
