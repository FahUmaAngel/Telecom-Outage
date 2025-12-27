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
        
        # Seed Regions
        for county in SWEDISH_COUNTIES:
            # county format: "Stockholms län"
            # Create bilingual name
            bilingual_name = create_bilingual_text(county)
            # Check if exists by Swedish name (key 'sv')
            existing = db.query(Region).filter(Region.name["sv"].as_string() == county).first()
            if not existing:
                logger.info(f"Seeding region: {county}")
                region = Region(name=bilingual_name)
                db.add(region)
                
        db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
