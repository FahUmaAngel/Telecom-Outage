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
        
        # Click "Större störningar hos Telenor" accordion
        try:
            acc = driver.find_element(By.XPATH, "//*[contains(text(), 'Större störningar')]")
            driver.execute_script("arguments[0].scrollIntoView();", acc)
            driver.execute_script("arguments[0].click();", acc)
            time.sleep(2)
        except Exception as e:
            print("Failed to click accordion:", e)
            
        driver.save_screenshot("telenor_step1.png")
            
        # Click the first county's spyglass/zoom
        try:
            zoom = driver.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
            driver.execute_script("arguments[0].click();", zoom)
            time.sleep(5)
        except Exception as e:
            print("Failed to click zoom:", e)
            
        driver.save_screenshot("telenor_step2.png")
        with open("telenor_step2.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)
            
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
