from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--window-size=1920,1080')
opts.add_argument('user-agent=Mozilla/5.0')

driver = webdriver.Chrome(options=opts)

print("1. Loading portal...")
driver.get('https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage')
time.sleep(5)

frames = driver.find_elements(By.TAG_NAME, 'iframe')
iframe_src = frames[0].get_attribute('src')
print(f"2. Found iframe src: {iframe_src}")

print("3. Navigating to iframe directly...")
driver.get(iframe_src)
time.sleep(5)

print("4. Clicking Nätverksstatus...")
try:
    tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Nätverksstatus')]")
    driver.execute_script("arguments[0].click();", tab)
    time.sleep(3)
except Exception as e:
    print("Tab:", e)

print("5. Clicking Historik...")
try:
    hist = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'H', 'h'), 'historik')]")
    driver.execute_script("arguments[0].click();", hist)
    time.sleep(3)
except Exception as e:
    print("Hist:", e)

html = driver.page_source
with open('telia_iframe.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved to telia_iframe.html")

driver.quit()
