"""
Migration script: Add Norwegian/Danish regions and fix Unknown locations in Supabase.
Run with: DATABASE_URL=<supabase_url> python scripts/migrate_regions_and_locations.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Region, Outage

NORWEGIAN_REGIONS = [
    {"sv": "Oslo", "en": "Oslo"},
    {"sv": "Viken", "en": "Viken"},
    {"sv": "Innlandet", "en": "Innlandet"},
    {"sv": "Vestfold og Telemark", "en": "Vestfold og Telemark"},
    {"sv": "Agder", "en": "Agder"},
    {"sv": "Rogaland", "en": "Rogaland"},
    {"sv": "Vestland", "en": "Vestland"},
    {"sv": "Møre og Romsdal", "en": "Møre og Romsdal"},
    {"sv": "Trøndelag", "en": "Trøndelag"},
    {"sv": "Nordland fylke", "en": "Nordland"},
    {"sv": "Narvik, Nordland", "en": "Narvik, Nordland"},
    {"sv": "Troms og Finnmark", "en": "Troms og Finnmark"},
]

DANISH_REGIONS = [
    {"sv": "Region Hovedstaden", "en": "Capital Region of Denmark"},
    {"sv": "Region Sjælland", "en": "Region Zealand"},
    {"sv": "Region Syddanmark", "en": "Region of Southern Denmark"},
    {"sv": "Region Midtjylland", "en": "Central Denmark Region"},
    {"sv": "Region Nordjylland", "en": "North Denmark Region"},
]

# Manual location fixes: incident_id -> (location, sv_region_name)
LOCATION_FIXES = {
    "INCSE0550247": ("Region Hovedstaden", "Region Hovedstaden"),
    "INCSE0555241": ("Region Hovedstaden", "Region Hovedstaden"),
    "INCSE0558549": ("Region Hovedstaden", "Region Hovedstaden"),
    "INCSE0570758": ("Trøndelag",          "Trøndelag"),
    "INCSE0577994": ("Hallands län",        "Hallands län"),
    "INCSE0582852": ("Gävleborgs län",      "Gävleborgs län"),
    "INCSE0584200": ("Dalarnas län",        "Dalarnas län"),
    "INCSE0588493": ("Region Hovedstaden", "Region Hovedstaden"),
    "INCSE0589126": ("Skåne län",           "Skåne län"),
    "INCSE0590729": ("Dalarnas län",        "Dalarnas län"),
    "INCSE0591460": ("Innlandet",           "Innlandet"),
    "INCSE0591623": ("Skåne län",           "Skåne län"),
    "INCSE0591760": ("Dalarnas län",        "Dalarnas län"),
    "INCSE0592354": ("Hallands län",        "Hallands län"),
    # Norwegian/Danish outages with correct location but missing region_id
    "INCSE0529035": ("Nordland fylke",      "Nordland fylke"),
    "INCSE0529036": ("Nordland fylke",      "Nordland fylke"),
    "INCSE0529040": ("Nordland fylke",      "Nordland fylke"),
    "INCSE0529038": ("Narvik, Nordland",    "Narvik, Nordland"),
}

def run():
    db = SessionLocal()
    try:
        # Step 1: Add Norwegian and Danish regions
        print("=== Step 1: Seeding Norwegian/Danish regions ===")
        added = 0
        for name in NORWEGIAN_REGIONS + DANISH_REGIONS:
            existing = db.query(Region).filter(
                Region.name["sv"].as_string() == name["sv"]
            ).first()
            if not existing:
                db.add(Region(name=name))
                print(f"  Added: {name['sv']}")
                added += 1
            else:
                print(f"  Already exists: {name['sv']} (id={existing.id})")
        db.commit()
        print(f"  Done: {added} regions added.\n")

        # Step 2: Build region lookup map
        all_regions = db.query(Region).all()
        region_map = {}
        for r in all_regions:
            name = r.name if isinstance(r.name, dict) else {}
            sv = name.get("sv", "").lower()
            region_map[sv] = r.id

        # Step 3: Fix outage locations
        print("=== Step 2: Fixing outage locations ===")
        updated = 0
        for inc_id, (location, region_sv) in LOCATION_FIXES.items():
            o = db.query(Outage).filter(Outage.incident_id == inc_id).first()
            if not o:
                print(f"  SKIP (not found): {inc_id}")
                continue
            rid = region_map.get(region_sv.lower())
            o.location = location
            o.region_id = rid
            print(f"  {inc_id}: location={location!r}, region_id={rid}")
            updated += 1
        db.commit()
        print(f"  Done: {updated} outages updated.\n")

        print("=== Migration complete ===")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
