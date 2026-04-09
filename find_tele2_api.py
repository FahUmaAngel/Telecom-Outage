"""
Scan the Tele2 CDN micro-frontend JS bundle for the outage/ticket API URL.
"""
import urllib.request
import json
import re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 1. Get assets manifest  
manifest_url = "https://cdn.tele2.se/disturbance-map-mfe/vite/assets-manifest.json"
req = urllib.request.Request(manifest_url, headers=headers)
with urllib.request.urlopen(req) as r:
    manifest = json.loads(r.read().decode("utf-8"))

print("Manifest entries:")
for k, v in manifest.items():
    print(f"  {k}: {v}")

# 2. Find the main JS bundle
js_files = []
for key, val in manifest.items():
    if isinstance(val, str) and val.endswith(".js"):
        js_files.append(val)

print(f"\nJS files found: {js_files}")

# 3. Scan each JS file for API URLs
cdn_base = "https://cdn.tele2.se/disturbance-map-mfe/vite/"
for js_rel in js_files:
    js_url = cdn_base + js_rel if not js_rel.startswith("http") else js_rel
    print(f"\nScanning: {js_url}")
    try:
        req = urllib.request.Request(js_url, headers=headers)
        with urllib.request.urlopen(req) as r:
            js_text = r.read().decode("utf-8")
        
        # Find URLs related to outages, tickets, faults, disturbances
        keywords = ["ticket", "outage", "fault", "disturb", "störning", "incident", "AreaTicket", "GetTicket"]
        found = set()
        for kw in keywords:
            matches = re.findall(r'["\']([^"\']*' + kw + r'[^"\']*)["\']', js_text, re.IGNORECASE)
            for m in matches:
                if "/" in m or "api" in m.lower():
                    found.add(m)
        
        if found:
            print("  Found endpoints/strings:")
            for f in sorted(found):
                print(f"    {f}")
        else:
            print("  No outage API strings found in this file")
            # Show any API url found
            api_urls = re.findall(r'"(https?://[^"]*api[^"]*)"', js_text)
            if api_urls:
                print("  Other API URLs:")
                for u in set(api_urls)[:10]:
                    print(f"    {u}")
    except Exception as e:
        print(f"  Error: {e}")
