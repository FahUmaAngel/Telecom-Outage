"""
Telia Historical Scraper (2025-2026)
Fetches past network outages using Telia's GetFaultTimeline and GetLocationInfoHistoric APIs.
"""
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_BASE = "https://coverage.ddc.teliasonera.net/coverageportal_se"
HISTORIC_INFO_URL = f"{API_BASE}/Outage/GetLocationInfoHistoric"

# Predefined coordinates for major counties (approximate center)
COUNTY_COORDS = [
    {"name": "Stockholm", "lat": 59.3326, "lon": 18.0649},
    {"name": "Västra Götaland", "lat": 57.7089, "lon": 11.9746},
    {"name": "Skåne", "lat": 55.6044, "lon": 13.0038},
    {"name": "Uppsala", "lat": 59.8586, "lon": 17.6389},
    {"name": "Östergötland", "lat": 58.4108, "lon": 15.6214},
    {"name": "Jönköping", "lat": 57.7826, "lon": 14.1618},
    {"name": "Kronoberg", "lat": 56.8777, "lon": 14.8091},
    {"name": "Kalmar", "lat": 56.6634, "lon": 16.3568},
    {"name": "Gotland", "lat": 57.6348, "lon": 18.2948},
    {"name": "Blekinge", "lat": 56.1612, "lon": 15.5869},
    {"name": "Halland", "lat": 56.6745, "lon": 12.8578},
    {"name": "Värmland", "lat": 59.3793, "lon": 13.5036},
    {"name": "Örebro", "lat": 59.2735, "lon": 15.2134},
    {"name": "Västmanland", "lat": 59.6100, "lon": 16.5448},
    {"name": "Dalarna", "lat": 60.6062, "lon": 15.6264},
    {"name": "Gävleborg", "lat": 60.6749, "lon": 17.1413},
    {"name": "Västernorrland", "lat": 62.6323, "lon": 17.9379},
    {"name": "Jämtland", "lat": 63.1792, "lon": 14.6358},
    {"name": "Västerbotten", "lat": 63.8258, "lon": 20.2630},
    {"name": "Norrbotten", "lat": 65.5848, "lon": 22.1567}
]

class TeliaHistoricalScraper:
    def __init__(self, ert_token: str, session_id: str):
        self.ert_token = ert_token
        self.session_id = session_id
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage"
        })
        self.session.cookies.set("JSESSIONID", session_id)

    def get_historical_outages(self, lat: float, lon: float, date: datetime):
        """Fetches historical outages for a specific location and date."""
        # Adjust for UTC
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        utc_start = start_date - timedelta(hours=2) # Rough approximation (UTC+2 for summer)
        utc_end = utc_start + timedelta(days=1, microseconds=-1)
        
        params = {
            "northing": f"{lat:.5f}",
            "easting": f"{lon:.5f}",
            "services": "NR700_DATANSA,NR3500_DATANSA,LTE800_DATA,LTE1800_DATA,LTE2600_DATA,GSM900_VOICE",
            "startDate": utc_start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "endDate": utc_end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ert": self.ert_token,
            "covQuality": "1"
        }
        
        try:
            logger.info(f"Fetching data for {date.date()} at {lat}, {lon}...")
            response = self.session.get(HISTORIC_INFO_URL, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                incidents = []
                services = data.get("Services", [])
                for svc in services:
                    fault_status = svc.get("HistoricFaultStatus")
                    if fault_status and fault_status.get("ServiceStatus") != "NORMAL_SERVICE":
                        fault_info = fault_status.get("NodeFaultInfo", {})
                        fault_ids = fault_info.get("FaultIds", [])
                        for fid in fault_ids:
                            incidents.append({
                                "incident_id": str(fid),
                                "service": svc.get("ServiceName"),
                                "status": fault_status.get("ServiceStatus"),
                                "start_time": utc_start.isoformat(),
                                "end_time": utc_end.isoformat(),
                                "location": f"{lat}, {lon}"
                            })
                return incidents
            else:
                logger.error(f"Failed to fetch: {response.status_code} - {response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None

    def scrape_range(self, start_date: datetime, end_date: datetime):
        """Iterates through range and locations to collect data."""
        all_incidents = []
        current_date = start_date
        
        while current_date <= end_date:
            logger.info(f"--- Processing Date: {current_date.date()} ---")
            for coord in COUNTY_COORDS:
                incidents = self.get_historical_outages(coord['lat'], coord['lon'], current_date)
                if incidents:
                    for inc in incidents:
                        inc['county'] = coord['name']
                        all_incidents.append(inc)
                time.sleep(0.5)
            
            current_date += timedelta(days=7) # Step by week
            
        return all_incidents

if __name__ == "__main__":
    # Read credentials
    ert = None
    jsid = None
    
    if os.path.exists(".telia_ert_token"):
        with open(".telia_ert_token", "r") as f:
            ert = f.read().strip()
    if os.path.exists(".telia_jsessionid"):
        with open(".telia_jsessionid", "r") as f:
            jsid = f.read().strip()
            
    if not ert or not jsid:
        print("Run get_telia_token.py first.")
        exit(1)
        
    scraper = TeliaHistoricalScraper(ert, jsid)
    
    # Test range: Feb 10 2026 to Feb 11 2026
    start = datetime(2026, 2, 10)
    end = datetime(2026, 2, 11)
    
    results = scraper.scrape_range(start, end)
    
    output_file = "telia_historical_incidents.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"Scraped {len(results)} incidents.")
