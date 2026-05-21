"""
Database initialization script.
Creates tables and seeds initial data.
"""
from .connection import engine, Base, SessionLocal
from .models import Operator, Region
from ..common.models import OperatorEnum
from ..common.translation import SWEDISH_COUNTIES, create_bilingual_text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed Operators
        for op_enum in OperatorEnum:
            name = op_enum.value
            existing = db.query(Operator).filter(Operator.name == name).first()
            if not existing:
                logger.info(f"Seeding operator: {name}")
                op = Operator(name=name)
                db.add(op)
        
        # Seed Swedish regions
        for county in SWEDISH_COUNTIES:
            bilingual_name = create_bilingual_text(county)
            existing = db.query(Region).filter(Region.name["sv"].as_string() == county).first()
            if not existing:
                logger.info(f"Seeding region: {county}")
                db.add(Region(name=bilingual_name))

        # Seed Norwegian regions
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

        # Seed Danish regions
        DANISH_REGIONS = [
            {"sv": "Region Hovedstaden", "en": "Capital Region of Denmark"},
            {"sv": "Region Sjælland", "en": "Region Zealand"},
            {"sv": "Region Syddanmark", "en": "Region of Southern Denmark"},
            {"sv": "Region Midtjylland", "en": "Central Denmark Region"},
            {"sv": "Region Nordjylland", "en": "North Denmark Region"},
        ]

        for name in NORWEGIAN_REGIONS + DANISH_REGIONS:
            existing = db.query(Region).filter(Region.name["sv"].as_string() == name["sv"]).first()
            if not existing:
                logger.info(f"Seeding region: {name['sv']}")
                db.add(Region(name=name))
                
        db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.exception(f"Error initializing DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
