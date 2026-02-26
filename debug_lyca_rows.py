import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def run():
    o = Options()
    o.add_argument('--headless')
    o.add_argument('--window-size=1920,1080')
    d = webdriver.Chrome(options=o)
    
    try:
        d.get('https://mboss.telenor.se/coverageportal?appmode=outage')
        time.sleep(10)
        
        acc = d.find_element(By.XPATH, "//button[contains(., 'I följande län')]")
        d.execute_script('arguments[0].click();', acc)
        time.sleep(2)
        
        zoom = d.find_element(By.CSS_SELECTOR, "i.fa-search, .fa-search")
        d.execute_script('arguments[0].click();', zoom)
        time.sleep(5)
        
        rows = d.find_elements(By.XPATH, '//table//tbody//tr')
        print(f'Total tr: {len(rows)}')
        
        for idx, r in enumerate(rows[:20]):
            text = r.text.strip().replace('\n', ' | ')
            print(f"TR {idx} TEXT: {text}")
            
    except Exception as e:
        print("ERROR:", e)
    finally:
        d.quit()

if __name__ == '__main__':
    run()
