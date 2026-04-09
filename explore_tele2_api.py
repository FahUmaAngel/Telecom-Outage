"""
Tele2 MIM API Explorer - fetches Tele2's internal map tile data 
to identify regions with disruptions, then builds regional incidents.
"""
import requests
import json
from datetime import datetime
import hashlib
from typing import List, Dict, Optional
import itertools

MIM_BASE = "https://mim.tele2.com/MIMCore/api"

# Sweden's bounding box in map tiles at zoom=5
# Zoom 5 gives us 6x6 tiles covering Sweden
SWEDEN_TILES_Z5 = [
    (x, y) for x, y in itertools.product(range(14, 20), range(7, 10))
]

# Map impactId to severity
IMPACT_MAP = {
    1: 'active',     # Avbrott i tjänsten (Full outage)
    2: 'active',     # Störning i tjänsten (Serious disruption)
    3: 'scheduled',  # Planerat avbrott (Planned)
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.tele2.se/',
    'Origin': 'https://www.tele2.se',
}

def fetch_tile(x: int, y: int, z: int = 5) -> Optional[dict]:
    """Fetch a single map tile from MIM API."""
    dt = datetime.utcnow().strftime('%Y%d%m%H%M')
    url = (
        f"{MIM_BASE}/Tile/GetOverlay"
        f"?x={x}&y={y}&z={z}"
        f"&viewType=3"
        f"&elementTechnologies=4,5"
        f"&impactIds=1,2,3"
        f"&countryCode=SWE"
        f"&currentServiceLayerNo=100"
        f"&dt={dt}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            ct = r.headers.get('Content-Type', '')
            if 'json' in ct:
                return r.json()
            # Tile images (PNG) mean no data in tile - skip
            return None
    except Exception as e:
        print(f"Error fetching tile ({x},{y}): {e}")
    return None


def fetch_outage_list() -> List[Dict]:
    """Try the MIM outage list endpoint directly."""
    endpoints = [
        f"{MIM_BASE}/Outage/GetOutages?countryCode=SWE",
        f"{MIM_BASE}/Outage/List?countryCode=SWE",
        f"{MIM_BASE}/Disturbance/GetAll?countryCode=SWE",
        f"{MIM_BASE}/Event/GetAll?countryCode=SWE",
        f"{MIM_BASE}/Status/GetAll?countryCode=SWE",
        "https://mim.tele2.com/MIMCore/api/Tile/GetTileInfo?countryCode=SWE",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            print(f"Tried: {url} -> Status: {r.status_code} | CT: {r.headers.get('Content-Type','')}")
            if r.status_code == 200 and 'json' in r.headers.get('Content-Type', ''):
                data = r.json()
                print(f"  -> Got JSON data: {str(data)[:300]}")
                return data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"  -> Error: {e}")
    return []

def make_tele2_id(region: str, impact: int) -> str:
    """Generate a deterministic Tele2 incident ID."""
    raw = f"tele2_{region}_{impact}_{datetime.utcnow().strftime('%Y%m%d')}"
    return f"TELE2-{hashlib.md5(raw.encode()).hexdigest()[:6].upper()}"


def main():
    print("=" * 60)
    print("Tele2 MIM API Scraper")
    print("=" * 60)
    
    # 1. Try direct outage list endpoint
    print("\n[1] Trying direct outage list endpoints...")
    outage_list = fetch_outage_list()
    if outage_list:
        print(f"  Found {len(outage_list)} outages from list endpoint!")
        return outage_list
    
    # 2. Scan all Swedish map tiles
    print(f"\n[2] Scanning {len(SWEDEN_TILES_Z5)} Sweden map tiles (z=5)...")
    tile_results = []
    for x, y in SWEDEN_TILES_Z5:
        data = fetch_tile(x, y)
        if data:
            print(f"  Tile ({x},{y}) returned JSON: {str(data)[:200]}")
            tile_results.append({'tile': (x, y), 'data': data})
    
    print(f"\n  Tiles with JSON data: {len(tile_results)}")
    for t in tile_results:
        print(f"  Tile {t['tile']}: {t['data']}")
    
    return tile_results

if __name__ == '__main__':
    result = main()
    print(f"\nFinal result: {len(result)} items")
