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


def extract_incident_row(cells, location, date_label):
    """Parses a single table row into an incident dict."""
    id_text = cells[0].get_text(strip=True)
    match = re.search(r'INCSE\d+', id_text)
    if not match: return None
    
    inc_id = match.group(0)
    desc = cells[1].get_text(strip=True).replace('Beskrivning', '').strip() if len(cells) > 1 else ''
    start = cells[2].get_text(strip=True).replace('Starttid', '').strip() if len(cells) > 2 else ''
    end = cells[3].get_text(strip=True).replace('Sluttid', '').strip() if len(cells) > 3 else ''
    
    return {
        'incident_id': inc_id,
        'operator': 'Telia',
        'source': f'telia_history_{date_label}',
        'status': 'resolved',
        'description': desc,
        'location': location or 'Sverige',
        'start_time': start,
        'estimated_end': end,
        'title': f"Incident {inc_id}"
    }

def extract_incidents_from_html(html: str, location: str = None, date_label: str = '') -> List[Dict]:
    """Extract INCSE incidents from an HTML page source."""
    incidents = []
    soup = BeautifulSoup(html, 'html.parser')

    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            inc = extract_incident_row(cells, location, date_label)
            if inc: incidents.append(inc)

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


def click_historical_tab(driver):
    """Clicks the Nätverkshistorik radio/button."""
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
                time.sleep(1.5)
                return True
            except Exception: pass
    return False

def set_date_via_js(driver, target_input, date_str):
    """Sets date using JS datepicker API or manual dispatch."""
    js_script = f"""
        var el = arguments[0];
        var dateStr = '{date_str}';
        try {{
            if (window.jQuery && window.jQuery(el).datepicker) {{
                window.jQuery(el).datepicker('setDate', dateStr);
                window.jQuery(el).trigger('changeDate');
            }} else {{
                el.value = dateStr;
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }} catch(e) {{}}
        try {{
            var btn = (el.parentElement || el.parentNode).querySelector('button');
            if(btn) btn.click();
        }} catch(e) {{}}
    """
    driver.execute_script(js_script, target_input)

def navigate_to_date(driver: webdriver.Chrome, target_date: datetime) -> bool:
    """Navigate the Nätverkshistorik date picker to a specific date."""
    date_str = target_date.strftime('%Y-%m-%d')
    logger.info(f"Navigating to {date_str}...")

    try:
        if not click_historical_tab(driver):
            logger.warning("Could not click Nätverkshistorik")
            return False

        time.sleep(1)
        date_inputs = driver.find_elements(By.XPATH, "//input[@type='text' or @type='date' or contains(@class, 'date')]")
        if not date_inputs: return False
            
        target_input = next((inp for inp in date_inputs if 'datum' in (inp.get_attribute('placeholder') or '').lower()), date_inputs[0])
        set_date_via_js(driver, target_input, date_str)
        
        try:
            target_input.clear()
            target_input.send_keys(date_str + Keys.ENTER)
        except Exception: pass
            
        time.sleep(5)
        logger.info(f"Date injected: {date_str}")
        return True
    except Exception as e:
        logger.exception(f"navigate_to_date error for {date_str}: {e}")
        return False


def expand_and_scrape_counties(driver, label, seen_ids):
    """Iterates through and expands county links to find more incidents."""
    incidents = []
    try:
        county_buttons = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
        logger.info(f"[{label}] Expanding {len(county_buttons)} county links...")
        for i in range(len(county_buttons)):
            try:
                btns = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
                if i >= len(btns): break
                btn = btns[i]
                
                # Identify county
                county_name = None
                try:
                    row_text = btn.find_element(By.XPATH, "./ancestor::tr//preceding-sibling::tr[1]").text
                    county_name = next((c for c in SWEDISH_COUNTIES if c.replace(' län', '') in row_text), None)
                except Exception: pass

                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.5)
                btn.click()
                time.sleep(3)

                county_incs = extract_incidents_from_html(driver.page_source, location=county_name, date_label=label)
                new = [inc for inc in county_incs if inc['incident_id'] not in seen_ids]
                seen_ids.update(inc['incident_id'] for inc in new)
                incidents.extend(new)

                driver.back()
                time.sleep(2)
            except (StaleElementReferenceException, Exception): continue
    except Exception: pass
    return incidents

def scrape_historical_date(driver: webdriver.Chrome, target_date: datetime, seen_ids: Set[str]) -> List[Dict]:
    """Scrape all incidents for a specific historical date."""
    label = target_date.strftime('%Y-%m-%d')
    incidents = []

    if navigate_to_date(driver, target_date):
        time.sleep(3)
        found = extract_incidents_from_html(driver.page_source, date_label=label)
        new = [i for i in found if i['incident_id'] not in seen_ids]
        seen_ids.update(i['incident_id'] for i in new)
        incidents.extend(new)
        logger.info(f"[{label}] Via date picker: {len(new)} new incidents")
    else:
        logger.info(f"[{label}] Falling back to page scan...")
        found = extract_incidents_from_html(driver.page_source, date_label=label)
        new = [i for i in found if i['incident_id'] not in seen_ids]
        seen_ids.update(i['incident_id'] for i in new)
        incidents.extend(new)

    incidents.extend(expand_and_scrape_counties(driver, label, seen_ids))
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

            day_incidents = scrape_historical_date(driver, target_date, seen_ids)
            result['outages'].extend(day_incidents)
            logger.info(f"[{label}] Added {len(day_incidents)} new incidents. Total so far: {len(result['outages'])}")

            # Small delay between days
            time.sleep(2)

        result['success'] = True

    except Exception as e:
        logger.exception(f"Fatal error: {e}", exc_info=True)
        result['error'] = str(e)
    finally:
        if driver:
            driver.quit()

    logger.info("\n" + "="*60)
    logger.info("SCRAPE COMPLETE")
    logger.info(f"Total unique incidents: {len(result['outages'])}")
    logger.info("="*60)

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
