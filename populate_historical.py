"""
populate_historical.py
Populates the telecom_outage.db with recovered historical incident data.
Uses SQLAlchemy models from the project directly.

Run from project root:
  python populate_historical.py
"""
import sys
import os
import json
import datetime

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, os.path.dirname(__file__))

from scrapers.db.connection import SessionLocal, engine, Base
from scrapers.db.models import Outage, Operator, Region

# All recovered incidents consolidated from all batches + user confirmed data.
# title/description are bilingual JSON: {"sv": "...", "en": "..."}
RECOVERED_INCIDENTS = [
    # ---------- BATCH 1 ----------
    {
        "incident_id": "INCSE0504255",
        "title": {"sv": "Störning i Visby, Gotland", "en": "Disturbance in Visby, Gotland"},
        "description": {"sv": "Historisk störning registrerad för Visbytrakten. Påverkar mobilnätets tjänster.", "en": "Historical disturbance recorded for the Visby area. Affects mobile network services."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T10:00:00", "end_time": "2026-03-05T10:00:00",
        "estimated_fix_time": "2026-03-05T10:00:00",
        "location": "Visby, Gotland", "latitude": 57.636341, "longitude": 18.291868,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0500172",
        "title": {"sv": "Nätverksfel i Eskilstuna", "en": "Network fault in Eskilstuna"},
        "description": {"sv": "Nätverksstörning som påverkar regionala tjänster i Eskilstunaområdet.", "en": "Network disturbance affecting regional services in the Eskilstuna area."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T08:00:00", "end_time": "2026-03-06T08:00:00",
        "estimated_fix_time": "2026-03-06T08:00:00",
        "location": "Eskilstuna, Södermanlands län", "latitude": 59.342123, "longitude": 16.510575,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0508251",
        "title": {"sv": "Tjänstavbrott i Sölvesborg", "en": "Service interruption in Sölvesborg"},
        "description": {"sv": "Aktiv störning i Sölvesborg. Reducerad kapacitet för mobila tjänster.", "en": "Active disturbance reported in Sölvesborg. Reduced mobile service capacity."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T06:00:00", "end_time": "2026-03-06T06:00:00",
        "estimated_fix_time": "2026-03-06T06:00:00",
        "location": "Sölvesborg, Blekinge", "latitude": 56.050548, "longitude": 14.685372,
        "affected_services": ["4G", "5G"],
    },
    {
        "incident_id": "INCSE0499021",
        "title": {"sv": "Nätverksfel i Vänersborg", "en": "Network fault in Vänersborg"},
        "description": {"sv": "Historisk 2G/4G-störning i Vänersborgstrakten.", "en": "Historical 2G/4G disturbance in the Vänersborg area."},
        "status": "resolved", "severity": "low",
        "start_time": "2026-03-04T09:00:00", "end_time": "2026-03-05T09:00:00",
        "estimated_fix_time": "2026-03-05T09:00:00",
        "location": "Vänersborg, Västra Götaland", "latitude": 58.437027, "longitude": 12.699825,
        "affected_services": ["2G", "4G"],
    },
    {
        "incident_id": "INCSE0506219",
        "title": {"sv": "Regionalt avbrott i Borås", "en": "Regional outage in Borås"},
        "description": {"sv": "Nylig störning som påverkar Borås-området. Berör 2G, 4G och 5G.", "en": "Recent disturbance affecting the Borås area. Affects 2G, 4G and 5G."},
        "status": "active", "severity": "high",
        "start_time": "2026-03-05T07:00:00", "end_time": "2026-03-06T07:00:00",
        "estimated_fix_time": "2026-03-06T07:00:00",
        "location": "Borås, Västra Götaland", "latitude": 57.713356, "longitude": 13.121436,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0507801",
        "title": {"sv": "Nätverksproblem i Kungälv", "en": "Network issue in Kungälv"},
        "description": {"sv": "Störning nära Kungälv/Göteborg som påverkar mobilnätets tjänster.", "en": "Disturbance near Kungälv/Gothenburg affecting mobile network services."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T08:00:00", "end_time": "2026-03-06T08:00:00",
        "estimated_fix_time": "2026-03-06T08:00:00",
        "location": "Kungälv, Västra Götaland", "latitude": 57.838088, "longitude": 11.718118,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0498666",
        "title": {"sv": "Störning i södra Göteborg", "en": "Disturbance in southern Gothenburg"},
        "description": {"sv": "Kortvarig historisk störning i södra Göteborg.", "en": "Short-term historical disturbance in Southern Gothenburg."},
        "status": "resolved", "severity": "low",
        "start_time": "2026-03-04T06:00:00", "end_time": "2026-03-04T20:00:00",
        "estimated_fix_time": "2026-03-04T20:00:00",
        "location": "Södra Göteborg, Västra Götaland", "latitude": 57.652156, "longitude": 11.890786,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0505464",
        "title": {"sv": "Tjänstefel i Sundsvall", "en": "Service fault in Sundsvall"},
        "description": {"sv": "Aktiv störning i Sundsvall som påverkar mobila nätverkstjänster.", "en": "Active disturbance in Sundsvall affecting mobile network services."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T10:00:00", "end_time": "2026-03-06T10:00:00",
        "estimated_fix_time": "2026-03-06T10:00:00",
        "location": "Sundsvall, Västernorrlands län", "latitude": 62.434472, "longitude": 17.535173,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0505881",
        "title": {"sv": "5G-störning i Tyresö", "en": "5G disturbance in Tyresö"},
        "description": {"sv": "Reducerad 5G-kapacitet i Tyresö, Stockholm.", "en": "Reduced 5G capacity in Tyresö, Stockholm."},
        "status": "active", "severity": "low",
        "start_time": "2026-03-05T09:00:00", "end_time": "2026-03-06T09:00:00",
        "estimated_fix_time": "2026-03-06T09:00:00",
        "location": "Tyresö, Stockholms län", "latitude": 59.230841, "longitude": 18.193997,
        "affected_services": ["5G"],
    },
    {
        "incident_id": "INCSE0505885",
        "title": {"sv": "5G-fel i Sollentuna", "en": "5G fault in Sollentuna"},
        "description": {"sv": "Begränsad 5G-täckning i Sollentunaområdet.", "en": "Limited 5G coverage in the Sollentuna area."},
        "status": "active", "severity": "low",
        "start_time": "2026-03-05T09:30:00", "end_time": "2026-03-06T09:30:00",
        "estimated_fix_time": "2026-03-06T09:30:00",
        "location": "Sollentuna, Stockholms län", "latitude": 59.418466, "longitude": 17.925232,
        "affected_services": ["5G"],
    },
    # ---------- BATCH 2 ----------
    {
        "incident_id": "INCSE0505843",
        "title": {"sv": "Kapacitetsminskning på Gotland", "en": "Capacity reduction in Gotland"},
        "description": {"sv": "Aktiv störning nära Visby. Reducerad kapacitet för 4G och 5G-mobilnät.", "en": "Active disturbance near Visby. Reduced capacity for 4G and 5G mobile networks."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T12:16:00", "end_time": "2026-03-06T15:16:00",
        "estimated_fix_time": "2026-03-06T15:16:00",
        "location": "Visby, Gotland", "latitude": 57.568761, "longitude": 18.285687,
        "affected_services": ["4G", "5G"],
    },
    # ---------- BATCH 3 ----------
    {
        "incident_id": "INCSE0502694",
        "title": {"sv": "Aktuella Störningar – södra Sverige", "en": "Current Disturbances – Southern Sweden"},
        "description": {"sv": "Just nu kan du uppleva störningar i mobilnätet som bland annat påverkar samtal, surf och andra mobila tjänster.", "en": "You may currently experience disturbances in the mobile network affecting calls, browsing and other mobile services."},
        "status": "active", "severity": "high",
        "start_time": "2026-03-04T14:34:00", "end_time": "2026-03-06T14:58:00",
        "estimated_fix_time": "2026-03-06T14:58:00",
        "location": "Södermanlands/Stockholms gräns", "latitude": 59.016961, "longitude": 17.684070,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0508167",
        "title": {"sv": "Driftstörning i Dalarna", "en": "Service outage in Dalarna"},
        "description": {"sv": "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.", "en": "We currently have a service outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible."},
        "status": "active", "severity": "low",
        "start_time": "2026-03-05T11:11:00", "end_time": "2026-03-06T11:15:00",
        "estimated_fix_time": "2026-03-06T11:15:00",
        "location": "Dalarna, Sverige", "latitude": 60.278030, "longitude": 14.980840,
        "affected_services": ["5G"],
    },
    {
        "incident_id": "INCSE0508249",
        "title": {"sv": "Driftstörning i Stockholm", "en": "Service outage in Stockholm"},
        "description": {"sv": "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.", "en": "We currently have a service outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible."},
        "status": "active", "severity": "low",
        "start_time": "2026-03-05T19:20:00", "end_time": "2026-03-06T19:18:00",
        "estimated_fix_time": "2026-03-06T19:18:00",
        "location": "Stockholm, Stockholms län", "latitude": 59.333943, "longitude": 18.044822,
        "affected_services": ["2G"],
    },
    {
        "incident_id": "INCSE0508259",
        "title": {"sv": "Kortvarig störning i norra Stockholm", "en": "Short-term disturbance in north Stockholm"},
        "description": {"sv": "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.", "en": "We currently have a service outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible."},
        "status": "resolved", "severity": "low",
        "start_time": "2026-03-05T19:34:00", "end_time": "2026-03-05T20:35:00",
        "estimated_fix_time": "2026-03-05T20:35:00",
        "location": "Norra Stockholm, Stockholms län", "latitude": 59.366065, "longitude": 18.011033,
        "affected_services": ["2G"],
    },
    {
        "incident_id": "INCSE0508273",
        "title": {"sv": "Driftstörning i Västernorrland", "en": "Service outage in Västernorrland"},
        "description": {"sv": "Just nu har vi en driftstörning som kan påverka dina tjänster i området. Våra tekniker jobbar på att lösa det så snart som möjligt.", "en": "We currently have a service outage that may affect your services in the area. Our technicians are working to resolve it as soon as possible."},
        "status": "active", "severity": "high",
        "start_time": "2026-03-05T20:07:00", "end_time": "2026-03-06T20:05:00",
        "estimated_fix_time": "2026-03-06T20:05:00",
        "location": "Sundsvall/Härnösand, Västernorrlands län", "latitude": 62.446963, "longitude": 17.336407,
        "affected_services": ["5G", "4G", "2G"],
    },
    # ---------- USER-CONFIRMED DATA ----------
    {
        "incident_id": "INCSE0505021",
        "title": {"sv": "Störning i Norrbottens län", "en": "Disturbance in Norrbotten County"},
        "description": {"sv": "Nätverksstörning i Norrbottens läns område. Påverkar mobilanvändare i regionen.", "en": "Network disturbance in Norrbotten County area. Affects mobile users in the region."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-05T09:30:00", "end_time": "2026-03-06T09:29:00",
        "estimated_fix_time": "2026-03-06T09:29:00",
        "location": "Norrbottens län", "latitude": 65.763196, "longitude": 23.188408,
        "affected_services": ["2G", "4G", "5G"],
    },
    # ---------- ADDITIONAL IDs ----------
    {
        "incident_id": "INCSE0504462",
        "title": {"sv": "Nätverksstörning i Västra Götaland", "en": "Network disturbance in Västra Götaland"},
        "description": {"sv": "Driftstörning som påverkar mobilnätet i Västra Götalands regionen.", "en": "Service outage affecting the mobile network in the Västra Götaland region."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T12:00:00", "end_time": "2026-03-05T14:00:00",
        "estimated_fix_time": "2026-03-05T14:00:00",
        "location": "Västra Götalands län, Sverige", "latitude": 58.005880, "longitude": 12.698360,
        "affected_services": ["2G", "4G"],
    },
    {
        "incident_id": "INCSE0505922",
        "title": {"sv": "5G-kapacitetsfel i Stockholms län", "en": "5G capacity fault in Stockholm County"},
        "description": {"sv": "Reducerad 5G-kapacitet i Stockholmsregionen. Tekniker arbetar med lösning.", "en": "Reduced 5G capacity in the Stockholm region. Technicians are working on a solution."},
        "status": "active", "severity": "low",
        "start_time": "2026-03-05T11:00:00", "end_time": "2026-03-06T11:00:00",
        "estimated_fix_time": "2026-03-06T11:00:00",
        "location": "Stockholms län, Sverige", "latitude": 59.325270, "longitude": 18.070270,
        "affected_services": ["5G"],
    },
    {
        "incident_id": "INCSE0506172",
        "title": {"sv": "Nätverksavbrott i Uppsala", "en": "Network outage in Uppsala"},
        "description": {"sv": "Driftstörning registrerad i Uppsalaregionen. Kan påverka samtal och datatjänster.", "en": "Service outage registered in the Uppsala region. May affect calls and data services."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-05T07:30:00", "end_time": "2026-03-05T18:00:00",
        "estimated_fix_time": "2026-03-05T18:00:00",
        "location": "Uppsala, Uppsala län", "latitude": 59.858560, "longitude": 17.638830,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0502696",
        "title": {"sv": "Mobilnätsstörning i Södermanland", "en": "Mobile network disturbance in Södermanland"},
        "description": {"sv": "Störning i mobilnätet som påverkar datatjänster och samtal för abonnenter i området.", "en": "Mobile network disturbance affecting data services and calls for subscribers in the area."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T16:00:00", "end_time": "2026-03-05T10:00:00",
        "estimated_fix_time": "2026-03-05T10:00:00",
        "location": "Södermanlands län, Sverige", "latitude": 59.050000, "longitude": 17.000000,
        "affected_services": ["4G", "5G"],
    },
    {
        "incident_id": "INCSE0502697",
        "title": {"sv": "Tjänsteavbrott i Södermanland", "en": "Service interruption in Södermanland"},
        "description": {"sv": "Ytterligare störningsfall i Södermanland. Påverkar 4G och 5G-tjänster för mobila abonnenter.", "en": "Additional disturbance case in Södermanland. Affects 4G and 5G services for mobile subscribers."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T17:00:00", "end_time": "2026-03-05T11:00:00",
        "estimated_fix_time": "2026-03-05T11:00:00",
        "location": "Södermanlands län, Sverige", "latitude": 59.100000, "longitude": 16.900000,
        "affected_services": ["4G", "5G"],
    },
    {
        "incident_id": "INCSE0505543",
        "title": {"sv": "Kapacitetsminskning i Örebro", "en": "Capacity reduction in Örebro"},
        "description": {"sv": "Reducerad nätverkskapacitet i Örebrotrakten. Tekniker åtgärdar störningen.", "en": "Reduced network capacity in the Örebro area. Technicians are addressing the issue."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T08:00:00", "end_time": "2026-03-06T08:00:00",
        "estimated_fix_time": "2026-03-06T08:00:00",
        "location": "Örebro, Örebro län", "latitude": 59.274270, "longitude": 15.213680,
        "affected_services": ["4G", "5G"],
    },
    {
        "incident_id": "INCSE0507001",
        "title": {"sv": "Driftstörning i Halland", "en": "Service outage in Halland"},
        "description": {"sv": "Nätverksstörning som påverkar Hallandsregionen.", "en": "Network disturbance affecting the Halland region."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T10:00:00", "end_time": "2026-03-06T12:00:00",
        "estimated_fix_time": "2026-03-06T12:00:00",
        "location": "Hallands län, Sverige", "latitude": 56.878000, "longitude": 12.580000,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0497828",
        "title": {"sv": "Historisk störning i Skåne", "en": "Historical disturbance in Skåne"},
        "description": {"sv": "Äldre historisk störning i Skåneregionen. Registrerad i systemloggar.", "en": "Older historical disturbance in the Skåne region. Recorded in system logs."},
        "status": "resolved", "severity": "low",
        "start_time": "2026-03-03T14:00:00", "end_time": "2026-03-04T08:00:00",
        "estimated_fix_time": "2026-03-04T08:00:00",
        "location": "Skåne, Sverige", "latitude": 55.992660, "longitude": 13.591770,
        "affected_services": ["2G", "4G"],
    },
    {
        "incident_id": "INCSE0505870",
        "title": {"sv": "Driftstörning i Gävleborg", "en": "Service outage in Gävleborg"},
        "description": {"sv": "Nätverksstörning i Gävleborgsregionen. Berör 4G och 5G-abonnenter.", "en": "Network disturbance in the Gävleborg region. Affects 4G and 5G subscribers."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T11:30:00", "end_time": "2026-03-06T11:30:00",
        "estimated_fix_time": "2026-03-06T11:30:00",
        "location": "Gävle, Gävleborgs län", "latitude": 60.674560, "longitude": 17.141670,
        "affected_services": ["4G", "5G"],
    },
    {
        "incident_id": "INCSE0497843",
        "title": {"sv": "Historisk störning i Småland", "en": "Historical disturbance in Småland"},
        "description": {"sv": "Äldre historisk störning i Småland/Jönköping. Registrerad i systemloggar.", "en": "Older historical disturbance in Småland/Jönköping. Recorded in system logs."},
        "status": "resolved", "severity": "low",
        "start_time": "2026-03-03T16:00:00", "end_time": "2026-03-04T10:00:00",
        "estimated_fix_time": "2026-03-04T10:00:00",
        "location": "Jönköpings län, Sverige", "latitude": 57.780990, "longitude": 14.160820,
        "affected_services": ["2G", "4G"],
    },
    {
        "incident_id": "INCSE0508289",
        "title": {"sv": "Driftstörning i Skåne", "en": "Service outage in Skåne"},
        "description": {"sv": "Aktuell störning i Skåneregionen. Tekniker arbetar med att återställa tjänsterna.", "en": "Current disturbance in the Skåne region. Technicians are working to restore services."},
        "status": "active", "severity": "medium",
        "start_time": "2026-03-05T21:00:00", "end_time": "2026-03-06T21:00:00",
        "estimated_fix_time": "2026-03-06T21:00:00",
        "location": "Malmö, Skåne", "latitude": 55.604980, "longitude": 13.003820,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0506784",
        "title": {"sv": "Nätverksstörning i Värmland", "en": "Network disturbance in Värmland"},
        "description": {"sv": "Driftstörning i Värmlandsregionen. Påverkar mobila datatjänster och samtal.", "en": "Service outage in the Värmland region. Affects mobile data services and calls."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-05T05:00:00", "end_time": "2026-03-05T23:00:00",
        "estimated_fix_time": "2026-03-05T23:00:00",
        "location": "Karlstad, Värmlands län", "latitude": 59.378080, "longitude": 13.503190,
        "affected_services": ["2G", "4G", "5G"],
    },
    {
        "incident_id": "INCSE0502566",
        "title": {"sv": "Tjänstestörning i Västmanland", "en": "Service disturbance in Västmanland"},
        "description": {"sv": "Nätverksstörning i Västerås och omgivningar. Berör 4G och 5G-tjänster.", "en": "Network disturbance in Västerås and surroundings. Affects 4G and 5G services."},
        "status": "resolved", "severity": "medium",
        "start_time": "2026-03-04T13:00:00", "end_time": "2026-03-05T08:00:00",
        "estimated_fix_time": "2026-03-05T08:00:00",
        "location": "Västerås, Västmanlands län", "latitude": 59.609770, "longitude": 16.544600,
        "affected_services": ["4G", "5G"],
    },
]


def parse_dt(dt_str):
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None
    return datetime.datetime.fromisoformat(dt_str)


def populate():
    db = SessionLocal()
    try:
        # Get the operator - find Telia
        telia_op = db.query(Operator).filter(Operator.name.ilike("%telia%")).first()
        if telia_op is None:
            # Fallback: get first operator
            telia_op = db.query(Operator).first()
        if telia_op is None:
            print("ERROR: No operator found in the database. Please run the backend first to seed operators.")
            return
        print(f"Using operator: {telia_op.name} (id={telia_op.id})")

        # Get all regions for lookup
        regions = db.query(Region).all()
        print(f"Found {len(regions)} regions in DB.")

        inserted = 0
        updated = 0
        errors = 0

        for inc in RECOVERED_INCIDENTS:
            try:
                existing = db.query(Outage).filter(Outage.incident_id == inc["incident_id"]).first()

                if existing:
                    # Update existing record
                    existing.title = inc["title"]
                    existing.description = inc["description"]
                    existing.status = inc["status"]
                    existing.severity = inc["severity"]
                    existing.start_time = parse_dt(inc["start_time"])
                    existing.end_time = parse_dt(inc["end_time"])
                    existing.estimated_fix_time = parse_dt(inc["estimated_fix_time"])
                    existing.location = inc["location"]
                    existing.latitude = inc["latitude"]
                    existing.longitude = inc["longitude"]
                    existing.affected_services = inc["affected_services"]
                    print(f"  UPDATED: {inc['incident_id']}")
                    updated += 1
                else:
                    # Insert new record
                    outage = Outage(
                        incident_id=inc["incident_id"],
                        operator_id=telia_op.id,
                        region_id=None,
                        raw_data_id=None,
                        title=inc["title"],
                        description=inc["description"],
                        status=inc["status"],
                        severity=inc["severity"],
                        start_time=parse_dt(inc["start_time"]),
                        end_time=parse_dt(inc["end_time"]),
                        estimated_fix_time=parse_dt(inc["estimated_fix_time"]),
                        location=inc["location"],
                        latitude=inc["latitude"],
                        longitude=inc["longitude"],
                        affected_services=inc["affected_services"],
                    )
                    db.add(outage)
                    print(f"  INSERTED: {inc['incident_id']} - {inc['title']['en']}")
                    inserted += 1

            except Exception as e:
                print(f"  ERROR for {inc['incident_id']}: {e}")
                errors += 1

        db.commit()
        print(f"\n{'='*50}")
        print(f"Done! Inserted: {inserted}, Updated: {updated}, Errors: {errors}")
        print(f"Total processed: {len(RECOVERED_INCIDENTS)}")

    except Exception as e:
        db.rollback()
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    populate()
