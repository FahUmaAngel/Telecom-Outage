"""
Telia Token Extractor (Improved)
Extracts the dynamic 'ert' token from the Telia coverage portal.
"""
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_telia_ert_token():
    """Starts a headless browser to grab the 'ert' token from the portal."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
    
    try:
        driver.get(url)
        # Wait for the page to load and scripts to execute
        time.sleep(20)
        
        # 1. Try common JS objects
        ert = driver.execute_script("""
            if (window.config && window.config.ert) return window.config.ert;
            if (window.appConfig && window.appConfig.ert) return window.appConfig.ert;
            // Search all properties in window for anything ending or containing 'ert'
            for (var key in window) {
                if (key.toLowerCase().includes('ert') && typeof window[key] === 'string' && window[key].length > 50) {
                    return window[key];
                }
            }
            return null;
        """)
        
        if not ert:
            # 2. Try to find it in script tags via regex
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                content = script.get_attribute("innerHTML")
                if content:
                    match = re.search(r'["\']?ert["\']?\s*[:=]\s*["\']([^"\']{50,})["\']', content)
                    if match:
                        ert = match.group(1)
                        break
        
        if not ert:
            # 3. Check cookies
            cookies = driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] == 'ert':
                    ert = cookie['value']
                    break
                    
        return ert
    finally:
        driver.quit()

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
    
    try:
        driver.get(url)
        time.sleep(20)
        
        # Extract ERT
        ert = driver.execute_script("""
            if (window.config && window.config.ert) return window.config.ert;
            for (var key in window) {
                if (key.toLowerCase().includes('ert') && typeof window[key] === 'string' && window[key].length > 50) {
                    return window[key];
                }
            }
            return null;
        """)
        
        # Extract JSESSIONID
        jsessionid = None
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'JSESSIONID':
                jsessionid = cookie['value']
                break
        
        if ert:
            print(f"Token found: {ert[:10]}...")
            with open(".telia_ert_token", "w") as f:
                f.write(ert)
        
        if jsessionid:
            print(f"JSESSIONID found: {jsessionid[:10]}...")
            with open(".telia_jsessionid", "w") as f:
                f.write(jsessionid)
        
        if not ert and not jsessionid:
            print("Credentials not found.")
            
    finally:
        driver.quit()
