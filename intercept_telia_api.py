"""
Intercept Telia's GetFaultTimeline API calls using Chrome DevTools Protocol.
When the page loads, Telia's JS calls GetFaultTimeline to get current outage data.
We capture this URL + any auth headers, then replay it with historical date ranges.
"""
import json
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PORTAL_URL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

def intercept_api():
    opts = Options()
    # Non-headless so we can see what's happening
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=opts)
    captured_requests = []
    
    try:
        # Enable CDP network monitoring
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setRequestInterception", {
            "patterns": [{"urlPattern": "*GetFaultTimeline*"}, {"urlPattern": "*fault*timeline*"}, {"urlPattern": "*FaultTimeline*"}]
        })
        
        print(f"Loading {PORTAL_URL}...")
        driver.get(PORTAL_URL)
        
        # Wait for page to fully load and make API calls
        time.sleep(15)
        
        # Capture performance logs (network requests)
        logs = driver.get_log('performance')
        
        api_urls = []
        api_headers = {}
        
        for log in logs:
            msg = json.loads(log['message'])
            method = msg.get('message', {}).get('method', '')
            params = msg.get('message', {}).get('params', {})
            
            # Look for network requests
            if method == 'Network.requestWillBeSent':
                req = params.get('request', {})
                url = req.get('url', '')
                if any(kw in url.lower() for kw in ['fault', 'timeline', 'outage', 'incident', 'incse', 'getfault']):
                    print(f"[API] Captured: {url[:120]}")
                    api_urls.append({
                        'url': url,
                        'headers': req.get('headers', {}),
                        'method': req.get('method', 'GET'),
                        'postData': req.get('postData', '')
                    })
            
            if method == 'Network.responseReceived':
                req_url = params.get('response', {}).get('url', '')
                if any(kw in req_url.lower() for kw in ['fault', 'timeline', 'outage']):
                    print(f"[RES] Response for: {req_url[:120]}")
        
        if not api_urls:
            print("\nNo API URLs captured from performance logs. Trying XHR interception via JS...")
            
            # Alternative: use JS to intercept XHR calls
            intercept_js = """
            window._capturedXHRs = [];
            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url) {
                if (url && (url.includes('Fault') || url.includes('fault') || url.includes('Timeline') || url.includes('outage'))) {
                    window._capturedXHRs.push({method: method, url: url});
                    console.log('XHR captured:', url);
                }
                return origOpen.apply(this, arguments);
            };
            
            // Also intercept fetch
            const origFetch = window.fetch;
            window.fetch = function(url, opts) {
                if (url && typeof url === 'string' && (url.includes('Fault') || url.includes('outage') || url.includes('Timeline'))) {
                    window._capturedXHRs.push({method: 'fetch', url: url});
                    console.log('Fetch captured:', url);
                }
                return origFetch.apply(this, arguments);
            };
            """
            driver.execute_script(intercept_js)
            
            # Reload page to trigger fresh API calls with our interceptors active
            driver.refresh()
            time.sleep(12)
            
            captured = driver.execute_script("return window._capturedXHRs || [];")
            print(f"\nXHR/Fetch captured: {len(captured)} calls")
            for c in captured:
                print(f"  [{c.get('method')}] {c.get('url', '')[:150]}")
                api_urls.append({'url': c.get('url', ''), 'method': c.get('method', 'GET')})
        
        # Also dump the page source looking for API base URLs
        page_src = driver.page_source
        
        # Look for the API host embedded in JS
        api_patterns = [
            r'https?://[^"\']+/api[^"\']*',
            r'https?://[^"\']+Timeline[^"\']*',
            r'https?://[^"\']+fault[^"\']*',
            r'"baseUrl"\s*:\s*"([^"]+)"',
            r"'baseUrl'\s*:\s*'([^']+)'",
            r'serviceUrl["\']?\s*[:=]\s*["\']([^"\']+)',
        ]
        
        found_urls = set()
        for pat in api_patterns:
            for m in re.findall(pat, page_src, re.IGNORECASE):
                if 'telia' in m.lower() or 'coverage' in m.lower() or 'ddc' in m.lower():
                    found_urls.add(m)
        
        if found_urls:
            print(f"\nFound {len(found_urls)} potential API URLs in page source:")
            for u in found_urls:
                print(f"  {u}")
        
        # Try cookies for session auth
        cookies = driver.get_cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        print(f"\nPage cookies: {list(cookie_dict.keys())}")
        
        # Save findings
        result = {
            'api_urls': api_urls,
            'found_in_source': list(found_urls),
            'cookies': list(cookie_dict.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        with open('telia_api_intercept.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved findings to telia_api_intercept.json")
        print(f"  API calls found: {len(api_urls)}")
        print(f"  URLs in source: {len(found_urls)}")
        
        return result
        
    finally:
        driver.quit()


if __name__ == '__main__':
    # Enable performance logging
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
    
    driver = webdriver.Chrome(options=opts)
    captured = []
    
    try:
        print(f"Loading {PORTAL_URL}...")
        driver.get(PORTAL_URL)
        time.sleep(12)
        
        # Check performance logs
        logs = driver.get_log('performance')
        print(f"Total performance log entries: {len(logs)}")
        
        api_hits = []
        for entry in logs:
            try:
                msg = json.loads(entry['message'])
                method = msg.get('message', {}).get('method', '')
                params = msg.get('message', {}).get('params', {})
                
                if method == 'Network.requestWillBeSent':
                    url = params.get('request', {}).get('url', '')
                    headers = params.get('request', {}).get('headers', {})
                    post_data = params.get('request', {}).get('postData', '')
                    
                    # Capture ALL XHR/API calls (not html, css, js assets)
                    if any(kw in url.lower() for kw in [
                        'api', 'getfault', 'timeline', 'outage', 'incident',
                        'coverageportal', 'fault', 'driftinfo'
                    ]) and not url.endswith(('.js', '.css', '.png', '.woff')):
                        print(f"  API: {url[:150]}")
                        api_hits.append({
                            'url': url,
                            'headers': dict(headers),
                            'post_data': post_data
                        })
            except Exception as e:
                pass
        
        print(f"\nAPI hits: {len(api_hits)}")
        
        # Also try XHR interception on a reload
        intercept_js = """
        window._apis = [];
        const origXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(m, u) {
            window._apis.push({type:'xhr', method: m, url: u});
            return origXHROpen.apply(this, arguments);
        };
        const origFetch = window.fetch;
        window.fetch = function(u, opts) {
            window._apis.push({type:'fetch', url: typeof u === 'string' ? u : u.url, method: opts && opts.method});
            return origFetch.apply(this, arguments);
        };
        """
        driver.execute_script(intercept_js)
        driver.refresh()
        time.sleep(12)
        
        js_captured = driver.execute_script("return window._apis || []")
        print(f"\nJS-captured API calls: {len(js_captured)}")
        
        interesting = [c for c in js_captured if not any(
            c.get('url', '').endswith(ext) for ext in ['.js', '.css', '.png', '.woff', '.map']
        ) and c.get('url', '')]
        
        for c in interesting[:30]:
            print(f"  [{c.get('type')} {c.get('method', 'GET')}] {c.get('url', '')[:150]}")
        
        # Save all
        output = {
            'perf_log_hits': api_hits,
            'js_intercepted': interesting,
            'timestamp': datetime.now().isoformat()
        }
        with open('telia_api_intercept.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved to telia_api_intercept.json")
        
    finally:
        driver.quit()
