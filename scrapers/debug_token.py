import requests
import re
import logging

logging.basicConfig(level=logging.INFO)

urls = {
    "telia": "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage",
    "lyca": "https://mboss.telenor.se/coverageportal?appmode=outage"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

for name, url in urls.items():
    print(f"\n--- Testing {name} ---")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        # Look for tokens
        for param in ['ert', 'rt']:
            # Search for rt=...
            matches = re.findall(rf'{param}=([^"\'&>\s]+)', resp.text)
            if matches:
                print(f"Found {param} matches: {matches[:3]}")
            
            # Search for assignments
            matches = re.findall(rf'{param}["\']?\s*[:=]\s*["\']([^"\']+)["\']', resp.text)
            if matches:
                print(f"Found {param} assignments: {matches[:3]}")
                
        # Save a snippet if not found
        found = False
        for param in ['ert', 'rt']:
             if f"{param}=" in resp.text: found = True
             
        if not found:
            print("No token found in response text. First 500 chars:")
            print(resp.text[:500])
            # Save the full HTML for manual inspection if needed
            with open(f"scrapers/debug_{name}.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"Saved full HTML to scrapers/debug_{name}.html")
            
    except Exception as e:
        print(f"Error: {e}")
