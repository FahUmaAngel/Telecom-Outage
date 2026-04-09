"""
Tele2 Diagnostic - reads the actual table/text content from the page
to understand the structure before writing the final scraper.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

TELE2_URL = "https://www.tele2.se/driftstorning-mobilnatet"

def diagnose():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(TELE2_URL)
    time.sleep(8)
    
    # Grab body text
    body = driver.find_element(By.TAG_NAME, 'body')
    body_text = body.text
    print("=== BODY TEXT ===")
    print(body_text[:3000])
    print("...")
    
    # Find all tables
    print("\n=== TABLES ===")
    tables = driver.find_elements(By.TAG_NAME, 'table')
    print(f"Tables found: {len(tables)}")
    for i, t in enumerate(tables):
        print(f"\nTable {i}: {t.text[:500]}")
    
    # Find any element mentioning "driftstörning" or "county" text
    print("\n=== LOOKING FOR OUTAGE DIVS ===")
    for sel in ['[data-testid]', 'h2', 'h3', 'article', 'section']:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in els:
            text = el.text.strip()
            if text and len(text) > 10:
                print(f"{sel}: {text[:150]}")

    driver.quit()

if __name__ == '__main__':
    diagnose()
