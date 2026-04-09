import time
from playwright.sync_api import sync_playwright

def check_ui_for_missing():
    fault_id = "INCSE0424369"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Opening portal to search for {fault_id}...")
        page.goto("https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage", wait_until="networkidle")
        time.sleep(2)
        
        try:
            # Type into the search input
            page.fill('input[placeholder="Sök adress, postnummer, ort eller händelse(INC)"]', fault_id)
            page.press('input[placeholder="Sök adress, postnummer, ort eller händelse(INC)"]', 'Enter')
            
            time.sleep(3)
            
            # Check if any cards or results exist on the page
            page_text = page.inner_text('body')
            if fault_id in page_text:
                print(f"Found {fault_id} in the page text!")
                
                # Try to extract the specific card text
                cards = page.query_selector_all('.card-content, .info-window, .search-result')
                for c in cards:
                    text = c.inner_text()
                    if fault_id in text:
                        print("--- CARD CONTENT ---")
                        print(text)
                        print("--------------------")
            else:
                print(f"[{fault_id}] Not found anywhere in the page text.")
                print("It appears Telia has purged this incident entirely from their frontend.")
                
        except Exception as e:
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    check_ui_for_missing()
