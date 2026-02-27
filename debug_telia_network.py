from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--window-size=1920,1080')
opts.add_argument('user-agent=Mozilla/5.0')
# Enable performance logging to capture network traffic
opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

print("Starting driver with network interception...")
driver = webdriver.Chrome(options=opts)

print("Loading portal...")
driver.get('https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage')
time.sleep(8)

# Get iframe
frames = driver.find_elements(By.TAG_NAME, 'iframe')
iframe_src = frames[0].get_attribute('src')
print(f"Navigating to iframe: {iframe_src}")
driver.get(iframe_src)
time.sleep(5)

print("Clicking Nätverksstatus...")
try:
    tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Nätverksstatus')]")
    driver.execute_script("arguments[0].click();", tab)
    time.sleep(2)
except Exception as e: print("Tab:", e)

print("Clicking Historik...")
try:
    hist = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'H', 'h'), 'historik')]")
    driver.execute_script("arguments[0].click();", hist)
    time.sleep(2)
except Exception as e: print("Hist:", e)

print("Changing date to 2025-01-01 via JS...")
date_str = "2025-01-01"
target_input = driver.find_elements(By.XPATH, "//input[@type='text' or @type='date' or contains(@class, 'date')]")[1]

js_script = f"""
    var el = arguments[0];
    var dateStr = '{date_str}';
    if (window.jQuery && window.jQuery(el).datepicker) {{
        window.jQuery(el).datepicker('setDate', dateStr);
        window.jQuery(el).trigger('changeDate');
        window.jQuery(el).trigger('change');
    }} else {{
        el.value = dateStr;
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
    }}
"""
driver.execute_script(js_script, target_input)
time.sleep(6) # Give it time to fetch data

# Parse performance logs to find API calls
print("\n--- Analyzing Network Traffic ---")
logs = driver.get_log('performance')

api_calls = []
for entry in logs:
    log = json.loads(entry['message'])['message']
    if 'Network.responseReceived' in log['method']:
        resp = log['params']['response']
        url = resp['url']
        # Filter for API requests
        if 'api' in url.lower() or 'rest' in url.lower() or 'fault' in url.lower() or 'timeline' in url.lower() or 'coverage' in url.lower():
            if url.endswith('.png') or url.endswith('.jpg') or url.endswith('.css') or url.endswith('.js'): continue
            
            print(f"URL: {url}")
            try:
                # Get the response body via CDP
                request_id = log['params']['requestId']
                body = driver.execute('executeCdpCommand', {'cmd': 'Network.getResponseBody', 'params': {'requestId': request_id}})
                print(f"Body length: {len(body['value'])}")
                if len(body['value']) > 0 and len(body['value']) < 1000:
                    print(f"Body Preview: {body['value'][:300]}")
            except Exception as e:
                pass
            print("-" * 40)

driver.quit()
print("Done.")
