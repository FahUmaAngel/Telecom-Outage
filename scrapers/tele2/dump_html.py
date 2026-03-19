from playwright.sync_api import sync_playwright

def dump_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")
        
        print("Loading page...")
        page.goto("https://www.tele2.se/driftstorning-mobilnatet", wait_until="networkidle")
        
        try:
            page.locator("button:has-text('Acceptera alla')").click(timeout=3000)
            print("Cookies accepted.")
        except:
            pass
            
        print("Dumping body HTML...")
        html = page.evaluate("document.body.innerHTML")
        
        with open("tele2_body.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        browser.close()
        print("Saved to tele2_body.html")

if __name__ == "__main__":
    dump_html()
