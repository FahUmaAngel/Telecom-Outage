"""
Tele2 XHR interception - reads actual network responses from the page
using CDP (Chrome DevTools Protocol) to find the JSON data.
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

def intercept_xhr():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Enable CDP network
    driver.execute_cdp_cmd('Network.enable', {})
    
    # Store request IDs to retrieve body later
    xhr_responses = []
    
    driver.get(TELE2_URL)
    time.sleep(15)
    
    # Read all performance logs and capture XHR responses
    logs = driver.get_log('performance')
    
    json_responses = []
    for log in logs:
        try:
            msg = json.loads(log['message'])
            method = msg.get('message', {}).get('method', '')
            params = msg.get('message', {}).get('params', {})
            
            if method == 'Network.responseReceived':
                url = params.get('response', {}).get('url', '')
                ct = params.get('response', {}).get('mimeType', '')
                req_id = params.get('requestId', '')
                
                # Skip Google Maps tiles, images, etc.
                if any(skip in url for skip in ['maps.googleapis', '.png', '.jpg', '.css', 'font', 'gtm']):
                    continue
                    
                if 'json' in ct or 'tele2' in url or 'mim' in url:
                    try:
                        body = driver.execute_cdp_cmd(
                            'Network.getResponseBody',
                            {'requestId': req_id}
                        )
                        body_text = body.get('body', '')
                        if body_text and len(body_text) > 10:
                            print(f"\n=== RESPONSE ===")
                            print(f"URL: {url}")
                            print(f"CT: {ct}")
                            print(f"Body: {body_text[:1000]}")
                            json_responses.append({
                                'url': url,
                                'body': body_text[:2000]
                            })
                    except Exception as ex:
                        pass
        except:
            pass
    
    # Also look for any window.___ data injected by the app
    try:
        app_data = driver.execute_script("""
            var result = {};
            // Check for common state containers
            if (window.__NEXT_DATA__) result.next_data = JSON.stringify(window.__NEXT_DATA__).substring(0, 1000);
            if (window.__nuxt) result.nuxt = 'found';
            if (window.__APP_DATA__) result.app_data = JSON.stringify(window.__APP_DATA__).substring(0, 1000);
            if (window.outages) result.outages = JSON.stringify(window.outages).substring(0, 1000);
            if (window.disturbances) result.disturbances = JSON.stringify(window.disturbances).substring(0, 1000);
            
            // Check Astro (framework used by Tele2)
            var keys = Object.keys(window).filter(k => k.includes('data') || k.includes('store') || k.includes('state'));
            result.window_keys = keys.slice(0, 20).join(',');
            return result;
        """)
        print("\n=== WINDOW DATA ===")
        print(json.dumps(app_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error accessing window data: {e}")
    
    print(f"\n=== TOTAL JSON RESPONSES: {len(json_responses)} ===")
    
    driver.quit()
    return json_responses

if __name__ == '__main__':
    intercept_xhr()
