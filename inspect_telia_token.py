import requests
import re

def inspect_token():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    r = s.get("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage")
    
    # Let's search for "ert" or "ert=" or hidden inputs
    print("Inputs in page:")
    inputs = re.findall(r'<input[^>]+>', r.text)
    for i in inputs:
        print(i)
        
    print("\nScripts containing 'ert':")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
    for sc in scripts:
        if 'ert' in sc or 'token' in sc.lower():
            print(sc[:200] + "...")
            
    # Maybe it's standard ASP.NET RequestVerificationToken?
    rvt = re.findall(r'__RequestVerificationToken[^>]+value=["\']([^"\']+)["\']', r.text)
    print(f"\nRequestVerificationToken: {rvt}")

if __name__ == "__main__":
    inspect_token()
