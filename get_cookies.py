import json
from playwright.sync_api import sync_playwright

def get_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        print("Navigating to get cookies...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="domcontentloaded")
        time.sleep(5)
        cookies = context.cookies()
        browser.close()
        return cookies

if __name__ == "__main__":
    import time
    cookies = get_cookies()
    with open("telia_cookies.json", "w") as f:
        json.dump(cookies, f)
    print("Cookies saved.")
