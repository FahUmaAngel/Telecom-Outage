"""
Tele2 Network Interceptor - captures API calls made by the page
to find the actual disruption data endpoint.
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

def intercept_network():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Enable performance logging to capture network events
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Enable CDP (Chrome DevTools Protocol) Network tracking
    driver.execute_cdp_cmd('Network.enable', {})
    
    driver.get(TELE2_URL)
    time.sleep(12)  # Wait enough for all AJAX calls
    
    # Get performance logs
    logs = driver.get_log('performance')
    
    api_urls = set()
    for log in logs:
        try:
            msg = json.loads(log['message'])
            method = msg.get('message', {}).get('method', '')
            params = msg.get('message', {}).get('params', {})
            
            if method == 'Network.requestWillBeSent':
                url = params.get('request', {}).get('url', '')
                # Filter interesting API calls (not fonts, images, etc.)
                if any(keyword in url for keyword in [
                    'api', 'outage', 'driftstorning', 'coverage', 'disturbance',
                    'tele2.se', 'network', 'status', 'json', 'data'
                ]):
                    if not any(skip in url for skip in [
                        'google', 'facebook', 'analytics', 'gtm', 'font', 
                        '.css', '.png', '.jpg', '.svg', 'doubleclick'
                    ]):
                        api_urls.add(url)
                        
            # Also capture responses
            if method == 'Network.responseReceived':
                url = params.get('response', {}).get('url', '')
                content_type = params.get('response', {}).get('headers', {}).get('content-type', '')
                if 'json' in content_type and 'tele2' in url:
                    print(f"\nJSON Response from: {url}")
                    print(f"  Content-Type: {content_type}")
                    
        except Exception:
            pass
    
    print("=== API URLS CAPTURED ===")
    for url in sorted(api_urls):
        print(f"  - {url}")
    
    driver.quit()

if __name__ == '__main__':
    intercept_network()
