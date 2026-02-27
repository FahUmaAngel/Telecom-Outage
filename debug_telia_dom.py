import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--window-size=1920,1080')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

print("Starting driver...")
driver = webdriver.Chrome(options=opts)

try:
    print("Loading page...")
    driver.get('https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage')
    time.sleep(8)
    
    print("Clicking Nätverksstatus...")
    try:
        tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Nätverksstatus')]")
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(3)
    except Exception as e:
        print("Tab err:", e)

    print("Clicking Historik...")
    try:
        hist = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'H', 'h'), 'historik')]")
        driver.execute_script("arguments[0].click();", hist)
        time.sleep(3)
    except Exception as e:
        print("Hist err:", e)

    print("Dumping HTML...")
    html = driver.page_source
    with open('telia_debug_dom.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Saved telia_debug_dom.html")
finally:
    driver.quit()
