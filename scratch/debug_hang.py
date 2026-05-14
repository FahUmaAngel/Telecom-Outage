
import sys
import os

def log(msg):
    print(msg, flush=True)

log("Starting diagnostic...")
sys.path.append(".")

log("Importing settings...")
from scrapers.config import settings
log("Settings imported.")

log("Importing connection...")
from scrapers.db.connection import SessionLocal, engine
log("Connection imported.")

log("Testing DB connection...")
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
log("DB connection OK.")

log("Importing models...")
from scrapers.db.models import User
log("Models imported.")

log("Importing routers...")
from backend.routers import outages
log("Outages router imported.")
from backend.routers import operators
log("Operators router imported.")
from backend.routers import reports
log("Reports router imported.")
from backend.routers import analytics
log("Analytics router imported.")
from backend.routers import auth
log("Auth router imported.")
from backend.routers import regions
log("Regions router imported.")
from backend.routers import admin
log("Admin router imported.")

log("Importing main app...")
from backend.main import app
log("App imported successfully!")
