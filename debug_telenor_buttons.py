import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def run():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get("https://mboss.telenor.se/coverageportal?appmode=outage")
        time.sleep(10)
        
        # Print all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for b in buttons:
            text = b.text.strip().replace('\n', ' ')
            if text: print("Button:", text)
            
        print("-------")
        
        # Try to find Större störningar
        accs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Större')]")
        for a in accs:
            print("Found ACC:", a.tag_name, a.text.strip().replace('\n', ' '))
            
            # Click it!
            driver.execute_script("arguments[0].click();", a)
            time.sleep(3)
            
        print("-------")
        
        # Print all elements containing 'län'
        lans = driver.find_elements(By.XPATH, "//*[contains(text(), 'län')]")
        for l in lans:
            print("Found LÄN text in:", l.tag_name)
            
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
