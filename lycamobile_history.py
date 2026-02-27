"""
Lycamobile Historical Scraper
=============================
Scrapes Lycamobile (via Telenor Enghouse network) outage data.

Key facts:
- Lycamobile runs on Telenor's network
- Enghouse portal: https://mboss.telenor.se/coverageportal
- Telenor driftinfo: https://www.telenor.se/kundservice/driftinformation/
- No public historical archive exists - portal is live-only
- Data is accumulated over scraper runs

Run this periodically to build up historical data from today onward.
"""
import json
import logging
import time
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Set

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.db.connection import get_db
from scrapers.db.crud import save_outage

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("LycamobileHistory")

ENGHOUSE_URL = "https://mboss.telenor.se/coverageportal?appmode=outage"
TELENOR_DRIFT_URL = "https://www.telenor.se/kundservice/driftinformation/"

SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]

COUNTY_ALIASES = {
    "Stockholm": "Stockholms län",
    "Uppsala": "Uppsala län",
    "Södermanland": "Södermanlands län",
    "Östergötland": "Östergötlands län",
    "Jönköping": "Jönköpings län",
    "Kronoberg": "Kronobergs län",
    "Kalmar": "Kalmar län",
    "Gotland": "Gotlands län",
    "Blekinge": "Blekinge län",
    "Skåne": "Skåne län",
    "Halland": "Hallands län",
    "Västra Götaland": "Västra Götalands län",
    "Värmland": "Värmlands län",
    "Örebro": "Örebro län",
    "Västmanland": "Västmanlands län",
    "Dalarna": "Dalarnas län",
    "Gävleborg": "Gävleborgs län",
    "Västernorrland": "Västernorrlands län",
    "Jämtland": "Jämtlands län",
    "Västerbotten": "Västerbottens län",
    "Norrbotten": "Norrbottens län",
}


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=opts)


def find_county(text: str) -> str:
    """Find a Swedish county in text."""
    if not text:
        return 'Sverige'
    for county in SWEDISH_COUNTIES:
        if county in text or county.replace(' län', '') in text:
            return county
    for alias, county in COUNTY_ALIASES.items():
        if alias in text:
            return county
    return 'Sverige'


def scrape_enghouse_portal() -> List[Dict]:
    """Scrape the Lycamobile/Telenor Enghouse coverage portal for current outages."""
    logger.info("=" * 60)
    logger.info("Scraping Enghouse Portal (mboss.telenor.se)")
    logger.info("=" * 60)
    
    outages = []
    driver = make_driver()
    
    try:
        driver.get(ENGHOUSE_URL)
        time.sleep(8)
        
        # Extract token
        token = None
        src = driver.page_source
        for pattern in [r'["\']?rt["\']?\s*[:=]\s*["\']([^"\']+)', r'["\']?ert["\']?\s*[:=]\s*["\']([^"\']+)']:
            m = re.search(pattern, src)
            if m:
                token = m.group(1)
                logger.info(f"Token found: {token[:30]}...")
                break
        
        # Call AdminAreaList in-browser via JS
        if token:
            try:
                result = driver.execute_async_script("""
                    var cb = arguments[arguments.length - 1];
                    $.ajax({
                        url: '/coverageportal/Fault/AdminAreaList',
                        data: {
                            services: 'GSM_VOICE,GSM_DATA,UMTS_VOICE,UMTS_DATA,LTE_VOICE,LTE_DATA,5G_DATA,VoLTE',
                            faultsLastUpdated: '', cacheKey: '',
                            rt: '""" + token + """'
                        },
                        success: function(d) { cb({ok: true, data: d}); },
                        error: function(e) { cb({ok: false, status: e.status}); }
                    });
                """)
                
                logger.info(f"AdminAreaList response: {result}")
                
                if result and result.get('ok') and result.get('data'):
                    data = result['data']
                    areas = data if isinstance(data, list) else data.get('AdminAreas', data.get('areas', []))
                    
                    for area in (areas or []):
                        area_name = area.get('Name', area.get('name', 'Unknown'))
                        faults = area.get('Faults', area.get('faults', []))
                        
                        for fault in faults:
                            inc_id = (
                                fault.get('IncidentId') or
                                fault.get('Id') or
                                fault.get('FaultId') or
                                f"LYCA_{area_name}_{len(outages)}"
                            )
                            outages.append({
                                'incident_id': str(inc_id),
                                'location': area_name,
                                'description': str(fault.get('Description', '')),
                                'start_time': str(fault.get('StartTime', '')),
                                'end_time': str(fault.get('EndTime', '')),
                                'source': 'lyca_enghouse_api',
                                'raw': fault
                            })
                    
                    logger.info(f"API returned {len(outages)} faults")
            except Exception as e:
                logger.warning(f"AdminAreaList JS call failed: {e}")
        
        # Fallback: expand county links from page
        try:
            county_links = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
            logger.info(f"County links found: {len(county_links)}")
            
            seen = {o['incident_id'] for o in outages}
            
            for i in range(len(county_links)):
                try:
                    links = driver.find_elements(By.XPATH, "//a[contains(text(),'Visa område')]")
                    if i >= len(links):
                        break
                    
                    link = links[i]
                    try:
                        row_text = link.find_element(By.XPATH, "./ancestor::tr").text
                        county = find_county(row_text)
                    except:
                        county = 'Sverige'
                    
                    driver.execute_script("arguments[0].click()", link)
                    time.sleep(3)
                    
                    page_src = driver.page_source
                    # Get all IDs from this county page
                    found_ids = set(re.findall(r'[A-Z]{2,}\d{5,}', page_src)) - seen
                    
                    for inc_id in found_ids:
                        seen.add(inc_id)
                        outages.append({
                            'incident_id': inc_id,
                            'location': county,
                            'description': '',
                            'source': 'lyca_enghouse_county'
                        })
                    
                    driver.back()
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"County {i} expand error: {e}")
                    continue
        except Exception as e:
            logger.warning(f"County expansion failed: {e}")
        
        logger.info(f"Enghouse portal: {len(outages)} outages")
        return outages
        
    finally:
        driver.quit()


def scrape_telenor_driftinfo() -> List[Dict]:
    """Scrape Telenor's driftinfo page for current outages affecting Lycamobile."""
    logger.info("=" * 60)
    logger.info("Scraping Telenor Driftinfo (www.telenor.se)")
    logger.info("=" * 60)
    
    outages = []
    driver = make_driver()
    
    try:
        driver.get(TELENOR_DRIFT_URL)
        time.sleep(8)
        
        src = driver.page_source
        
        # Try to find __NEXT_DATA__
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', src, re.DOTALL)
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                page_props = next_data.get('props', {}).get('pageProps', {})
                
                # Look for disturbance/incident data
                for key in ['disturbances', 'outages', 'incidents', 'faults', 'driftinfo', 'content']:
                    if key in page_props and isinstance(page_props[key], list):
                        logger.info(f"Found {len(page_props[key])} items in '{key}'")
                        for i, item in enumerate(page_props[key]):
                            county = find_county(str(item))
                            inc_id = (
                                item.get('id') or
                                item.get('incidentId') or
                                item.get('caseId') or
                                f"TNR_{key}_{i}"
                            )
                            outages.append({
                                'incident_id': str(inc_id),
                                'location': county,
                                'description': str(item.get('description', item.get('title', str(item)[:200]))),
                                'start_time': str(item.get('startTime', item.get('createdAt', ''))),
                                'end_time': str(item.get('endTime', item.get('resolvedAt', ''))),
                                'source': 'telenor_driftinfo_nextjs'
                            })
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse __NEXT_DATA__: {e}")
        
        # Fallback: look for county mentions in rendered HTML
        if not outages:
            logger.info("No structured data found, scanning page text...")
            
            try:
                # Wait for any content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except TimeoutException:
                pass
            
            # Find elements that mention counties
            elements = driver.find_elements(By.XPATH, "//p|//h2|//h3|//li|//div[@class]")
            incident_count = 0
            
            for elem in elements:
                try:
                    text = elem.text.strip()
                    if len(text) < 10 or len(text) > 1000:
                        continue
                    
                    county = find_county(text)
                    if county != 'Sverige' and len(text) > 20:
                        inc_id = f"TNR_DRIFT_{incident_count:04d}"
                        incident_count += 1
                        
                        # Check for date info
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', text)
                        
                        outages.append({
                            'incident_id': inc_id,
                            'location': county,
                            'description': text[:300],
                            'start_time': date_match.group(0) if date_match else '',
                            'source': 'telenor_driftinfo_html'
                        })
                except Exception:
                    continue
        
        logger.info(f"Telenor driftinfo: {len(outages)} outages")
        return outages
        
    finally:
        driver.quit()


def ingest_outages(outages: List[Dict], db) -> tuple:
    """Ingest outages into the database."""
    saved = 0
    skipped = 0
    
    for outage in outages:
        try:
            inc_id = outage.get('incident_id')
            if not inc_id:
                skipped += 1
                continue
            
            location = outage.get('location', 'Sverige')
            county = find_county(location)
            final_location = county if county != 'Sverige' else location or 'Sverige'
            
            # Geocode
            coords = None
            if final_location != 'Sverige':
                coords = get_county_coordinates(
                    final_location if 'län' in final_location else final_location + ' län',
                    jitter=True
                )
            
            # Parse dates
            start_time = None
            end_time = None
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                for t_str in [outage.get('start_time', ''), '']:
                    if t_str:
                        try:
                            start_time = datetime.strptime(t_str.strip()[:19], fmt)
                            break
                        except ValueError:
                            continue
                if start_time:
                    break
            
            normalized = NormalizedOutage(
                operator=OperatorEnum.LYCAMOBILE,
                incident_id=inc_id,
                title={
                    'sv': f"Lycamobile driftstörning - {final_location}",
                    'en': f"Lycamobile outage - {final_location}"
                },
                description={
                    'sv': outage.get('description', ''),
                    'en': outage.get('description', '')
                },
                location=final_location,
                status=OutageStatus.ACTIVE,
                severity=SeverityLevel.MEDIUM,
                affected_services=['mobile', '4g'],
                source_url=ENGHOUSE_URL,
                started_at=start_time,
                estimated_fix_time=end_time,
                latitude=coords[0] if coords else None,
                longitude=coords[1] if coords else None,
            )
            
            save_outage(db, normalized, {'source': outage.get('source', 'lyca_history'), 'original': outage})
            saved += 1
            
        except Exception as e:
            logger.warning(f"Ingest error {outage.get('incident_id')}: {e}")
            skipped += 1
    
    return saved, skipped


def run_lycamobile_scrape(ingest: bool = True):
    """Run full Lycamobile scrape and optionally ingest into database."""
    logger.info("=" * 70)
    logger.info("LYCAMOBILE HISTORICAL SCRAPER")
    logger.info("=" * 70)
    
    all_outages = []
    seen_ids: Set[str] = set()
    
    # 1. Scrape Enghouse portal
    try:
        enghouse_outages = scrape_enghouse_portal()
        for o in enghouse_outages:
            if o['incident_id'] not in seen_ids:
                seen_ids.add(o['incident_id'])
                all_outages.append(o)
    except Exception as e:
        logger.error(f"Enghouse portal scrape failed: {e}")
    
    # 2. Scrape Telenor driftinfo
    try:
        drift_outages = scrape_telenor_driftinfo()
        for o in drift_outages:
            if o['incident_id'] not in seen_ids:
                seen_ids.add(o['incident_id'])
                all_outages.append(o)
    except Exception as e:
        logger.error(f"Telenor driftinfo scrape failed: {e}")
    
    logger.info(f"\n✓ Total unique Lycamobile outages: {len(all_outages)}")
    
    # Save to JSON
    result = {
        'outages': all_outages,
        'timestamp': datetime.now().isoformat(),
        'operator': 'Lycamobile',
        'success': True
    }
    
    output_file = 'lycamobile_history_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"✓ Saved to {output_file}")
    
    # Ingest into database
    if ingest and all_outages:
        logger.info("\nIngesting into database...")
        db = next(get_db())
        try:
            saved, skipped = ingest_outages(all_outages, db)
            db.commit()
            logger.info(f"✓ Ingested: {saved} saved, {skipped} skipped")
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            db.rollback()
        finally:
            db.close()
    elif not all_outages:
        logger.info("No outages found to ingest (portal shows no active outages)")
    
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Lycamobile Historical Scraper')
    parser.add_argument('--no-ingest', action='store_true', help='Skip database ingestion')
    args = parser.parse_args()
    
    run_lycamobile_scrape(ingest=not args.no_ingest)
