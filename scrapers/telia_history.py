"""
Telia Month-by-Month Historical Scraper
Scrapes incident data from Telia's 'Nätverkshistorik' feature
for each month from January 2025 to present.
"""
import json
import logging
import time
import re
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, NoSuchElementException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("TeliaHistory")

COVERAGE_PORTAL = "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"

SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=opts)


def extract_incidents_from_html(html: str, location: str = None, date_label: str = '') -> List[Dict]:
    """Extract INCSE incidents from an HTML page source."""
    incidents = []
    soup = BeautifulSoup(html, 'html.parser')

    # Primary: parse table rows
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            id_text = cells[0].get_text(strip=True)
            match = re.search(r'INCSE\d+', id_text)
            if match:
                inc_id = match.group(0)
                desc = cells[1].get_text(strip=True).replace('Beskrivning', '').strip() if len(cells) > 1 else ''
                start = cells[2].get_text(strip=True).replace('Starttid', '').strip() if len(cells) > 2 else ''
                end = cells[3].get_text(strip=True).replace('Sluttid', '').strip() if len(cells) > 3 else ''
                incidents.append({
                    'incident_id': inc_id,
                    'operator': 'Telia',
                    'source': f'telia_history_{date_label}',
                    'status': 'resolved',
                    'description': desc,
                    'location': location or 'Sverige',
                    'start_time': start,
                    'estimated_end': end,
                    'title': f"Incident {inc_id}"
                })

    # Fallback: regex scan for any INCSE IDs in the page
    if not incidents:
        for inc_id in set(re.findall(r'INCSE\d+', html)):
            incidents.append({
                'incident_id': inc_id,
                'operator': 'Telia',
                'source': f'telia_history_regex_{date_label}',
                'status': 'resolved',
                'location': location or 'Sverige',
                'title': f"Incident {inc_id}"
            })

    return incidents


def navigate_to_date(driver: webdriver.Chrome, wait: WebDriverWait, target_date: datetime) -> bool:
    """
    Navigate the Nätverkshistorik date picker to a specific date using robust JavaScript injection.
    Returns True if successful.
    """
    date_str = target_date.strftime('%Y-%m-%d')
    logger.info(f"Navigating to {date_str} via JS...")

    try:
        # 1. Click the 'Nätverkshistorik' radio/button
        hist_clicked = False
        for selector in [
            "//span[contains(text(), 'historik')]",
            "//label[contains(text(), 'historik')]",
            "//*[contains(text(), 'Nätverkshistorik')]",
            "//input[@type='radio' and following-sibling::*[contains(text(), 'historik')]]",
        ]:
            elems = driver.find_elements(By.XPATH, selector)
            for elem in elems:
                try:
                    driver.execute_script("arguments[0].click();", elem)
                    hist_clicked = True
                    time.sleep(1.5)
                    break
                except Exception:
                    pass
            if hist_clicked:
                break

        if not hist_clicked:
            logger.warning("Could not click Nätverkshistorik")
            return False

        time.sleep(1)

        # 2. Find date inputs
        date_inputs = driver.find_elements(By.XPATH, "//input[@type='text' or @type='date' or contains(@class, 'date')]")
        if not date_inputs:
            logger.warning("No date inputs found!")
            return False
            
        # Target the first likely date input
        target_input = None
        for inp in date_inputs:
            if 'datum' in (inp.get_attribute('placeholder') or '').lower() or 'date' in (inp.get_attribute('class') or '').lower():
                target_input = inp
                break
        
        if not target_input:
            target_input = date_inputs[0]
            
        # 3. Use JS to set the value. Since it's a bootstrap-datepicker, we must use its API if available.
        js_script = f"""
            var el = arguments[0];
            var dateStr = '{date_str}';
            
            try {{
                // Try jQuery bootstrap-datepicker API first
                if (window.jQuery && window.jQuery(el).datepicker) {{
                    window.jQuery(el).datepicker('setDate', dateStr);
                    window.jQuery(el).trigger('changeDate');
                    window.jQuery(el).trigger('change');
                }} else {{
                    // Fallback to manual event triggering
                    el.value = dateStr;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    
                    if (window.jQuery) {{
                        window.jQuery(el).trigger('change');
                    }}
                }}
            }} catch(e) {{
                console.error("Datepicker error", e);
            }}
            
            // Try clicking the button next to it (sometimes "Visa", "Sök", or calendar icon)
            try {{
                var parent = el.parentElement || el.parentNode;
                var btn = parent.querySelector('button');
                if(btn) btn.click();
            }} catch(e) {{}}
        """
        driver.execute_script(js_script, target_input)
        
        # Also try to send keys as a fallback if the JS failed
        try:
            target_input.clear()
            target_input.send_keys(date_str)
            target_input.send_keys(Keys.ENTER)
        except:
            pass
            
        time.sleep(5) # Wait for network request to load data
        
        logger.info(f"✓ Date injected: {date_str}")
        return True

    except Exception as e:
        logger.error(f"navigate_to_date JS error for {date_str}: {e}")
        return False


def scrape_historical_date(driver: webdriver.Chrome, wait: WebDriverWait, target_date: datetime, seen_ids: Set[str]) -> List[Dict]:
    """Scrape all incidents for a specific historical date."""
    label = target_date.strftime('%Y-%m-%d')
    incidents = []

    # Try to navigate to date via the Nätverkshistorik picker
    if navigate_to_date(driver, wait, target_date):
        time.sleep(3)
        page_html = driver.page_source
        found = extract_incidents_from_html(page_html, date_label=label)
        new = [i for i in found if i['incident_id'] not in seen_ids]
        seen_ids.update(i['incident_id'] for i in new)
        incidents.extend(new)
        logger.info(f"[{label}] Via date picker: {len(new)} new incidents")
    else:
        # Fallback: just try to click Nätverkshistorik and grab whatever is on the page
        logger.info(f"[{label}] Falling back to page scan...")
        page_html = driver.page_source
        found = extract_incidents_from_html(page_html, date_label=label)
        new = [i for i in found if i['incident_id'] not in seen_ids]
        seen_ids.update(i['incident_id'] for i in new)
        incidents.extend(new)

    # Also try expanding each county for active outages
    try:
        county_buttons = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
        logger.info(f"[{label}] Expanding {len(county_buttons)} county links...")
        for i in range(len(county_buttons)):
            try:
                btns = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
                if i >= len(btns):
                    break
                btn = btns[i]

                # Try to identify the county name
                county_name = None
                try:
                    row_text = btn.find_element(By.XPATH, "./ancestor::tr//preceding-sibling::tr[1]").text
                    for c in SWEDISH_COUNTIES:
                        if c.replace(' län', '') in row_text:
                            county_name = c
                            break
                except Exception:
                    pass

                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.5)
                btn.click()
                time.sleep(3)

                county_html = driver.page_source
                county_incs = extract_incidents_from_html(county_html, location=county_name, date_label=label)
                new = [i for i in county_incs if i['incident_id'] not in seen_ids]
                seen_ids.update(i['incident_id'] for i in new)
                incidents.extend(new)

                driver.back()
                time.sleep(2)
            except StaleElementReferenceException:
                continue
            except Exception as e:
                logger.warning(f"[{label}] County expand error {i}: {e}")
                continue
    except Exception:
        pass

    return incidents


def run_historical_scrape(start_year: int = 2025, start_month: int = 1) -> Dict:
    """
    Scrape all Telia incidents month by month from start_date to today.
    """
    result = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'date_range': f'{start_year}-{start_month:02d} to present',
        'success': False
    }

    seen_ids: Set[str] = set()
    current = datetime(start_year, start_month, 1)
    today = datetime.now().replace(day=1)

    driver = None
    try:
        logger.info("Starting Chrome...")
        driver = make_driver()
        wait = WebDriverWait(driver, 15)

        logger.info(f"Loading {COVERAGE_PORTAL} once for all dates...")
        driver.get(COVERAGE_PORTAL)
        time.sleep(6)

        try:
            tabs = driver.find_elements(By.XPATH, "//a[contains(text(),'Nätverksstatus')] | //a[contains(@href,'outage')]")
            for tab in tabs:
                if 'Nätverksstatus' in tab.text or 'outage' in tab.get_attribute('href', ''):
                    tab.click()
                    time.sleep(2)
                    break
        except Exception:
            pass

        all_dates = []
        d = current
        while d <= today:
            all_dates.append(d)
            # Advance 5 days to cover the month without making too many requests
            d += timedelta(days=5)

        logger.info(f"Will scrape {len(all_dates)} specific dates from {all_dates[0].strftime('%Y-%m-%d')} to {all_dates[-1].strftime('%Y-%m-%d')}")

        for target_date in all_dates:
            label = target_date.strftime('%Y-%m-%d')
            logger.info(f"\n{'='*50}")
            logger.info(f"Scraping date: {label}")
            logger.info(f"{'='*50}")

            day_incidents = scrape_historical_date(driver, wait, target_date, seen_ids)
            result['outages'].extend(day_incidents)
            logger.info(f"[{label}] Added {len(day_incidents)} new incidents. Total so far: {len(result['outages'])}")

            # Small delay between days
            time.sleep(2)

        result['success'] = True

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        result['error'] = str(e)
    finally:
        if driver:
            driver.quit()

    logger.info(f"\n{'='*60}")
    logger.info(f"SCRAPE COMPLETE")
    logger.info(f"Total unique incidents: {len(result['outages'])}")
    logger.info(f"{'='*60}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Telia Historical Scraper')
    parser.add_argument('--year', type=int, default=2025, help='Start year')
    parser.add_argument('--month', type=int, default=1, help='Start month')
    args = parser.parse_args()

    result = run_historical_scrape(start_year=args.year, start_month=args.month)

    output_file = 'telia_history_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"✓ Results saved to {output_file}")
    logger.info(f"  Total incidents: {len(result['outages'])}")
    if result['outages']:
        logger.info(f"  Sample: {result['outages'][0]['incident_id']} @ {result['outages'][0].get('location')}")
