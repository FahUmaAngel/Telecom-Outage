"""
Ingest telia_history_results.json into the outages database.
Handles geocoding, deduplication, and jitter.
"""
import json
import sys
import os
import re
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.common.geocoding import get_county_coordinates
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel
from scrapers.db.connection import get_db
from scrapers.db.crud import save_outage

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("IngestTeliaHistory")

COUNTY_ALIASES = {
    'Sverige': None,
    'Sweden': None,
}

SWEDISH_COUNTIES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län"
]


def parse_swedish_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    # Try common Swedish formats
    for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y %H:%M', '%d.%m.%Y %H:%M', '%Y-%m-%dT%H:%M:%S']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def find_county(text: str) -> str:
    """Find a Swedish county in a text string."""
    if not text:
        return 'Unknown'
    for county in SWEDISH_COUNTIES:
        if county in text or county.replace(' län', '') in text:
            return county
    # Try partial matches
    text_lower = text.lower()
    for county in SWEDISH_COUNTIES:
        base = county.replace(' län', '').lower()
        if base in text_lower:
            return county
    if text not in ('Sverige', 'Sweden', ''):
        return text
    return 'Unknown'


def ingest(results_file: str = 'telia_history_results.json'):
    if not os.path.exists(results_file):
        logger.error(f"File not found: {results_file}")
        return

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    outages = data.get('outages', [])
    logger.info(f"Loaded {len(outages)} incidents from {results_file}")

    db = next(get_db())
    saved = 0
    skipped = 0

    try:
        for outage in outages:
            try:
                incident_id = outage.get('incident_id')
                if not incident_id:
                    continue

                location_raw = outage.get('location', '')
                description = outage.get('description', '')
                title = outage.get('title', f"Incident {incident_id}")

                # Resolve location
                county = find_county(f"{location_raw} {description}")
                final_location = county if county != 'Unknown' else location_raw or 'Sverige'

                # Geocode
                coords = None
                if county not in ('Unknown', 'Sverige', 'Sweden'):
                    coords = get_county_coordinates(county, jitter=True)
                elif county == 'Unknown' and final_location:
                    # Try geocoding the raw location
                    for c in SWEDISH_COUNTIES:
                        if c.replace(' län', '') in final_location:
                            coords = get_county_coordinates(c, jitter=True)
                            county = c
                            break

                # Parse dates
                start_time = parse_swedish_date(outage.get('start_time'))
                end_time = parse_swedish_date(outage.get('estimated_end'))

                # If no start_time, try to extract year from source tag
                if not start_time:
                    src = outage.get('source', '')
                    date_match = re.search(r'(\d{4})-(\d{2})', src)
                    if date_match:
                        y, m = int(date_match.group(1)), int(date_match.group(2))
                        start_time = datetime(y, m, 1, 12, 0)

                normalized = NormalizedOutage(
                    operator=OperatorEnum.TELIA,
                    incident_id=incident_id,
                    title={'sv': title, 'en': title},
                    description={'sv': description, 'en': description},
                    location=final_location,
                    status=OutageStatus.RESOLVED,
                    severity=SeverityLevel.MEDIUM,
                    affected_services=['mobile'],
                    source_url='https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage',
                    started_at=start_time,
                    estimated_fix_time=end_time,
                    latitude=coords[0] if coords else None,
                    longitude=coords[1] if coords else None,
                )

                raw_data = {
                    'source': outage.get('source', 'telia_history'),
                    'scraped_at': data.get('timestamp'),
                    'original': outage
                }

                save_outage(db, normalized, raw_data)
                saved += 1

            except Exception as e:
                logger.warning(f"Error ingesting {outage.get('incident_id')}: {e}")
                skipped += 1

        db.commit()
        logger.info(f"\n✓ Ingestion complete!")
        logger.info(f"  Saved: {saved}")
        logger.info(f"  Skipped: {skipped}")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    ingest()
