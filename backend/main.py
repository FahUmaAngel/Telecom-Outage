"""
FastAPI Entry Point with Background Scheduler.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import outages, operators, reports, analytics, auth, regions, admin
from .middleware import LoggingMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys
import os
import logging

# Add project root to path for scraper imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scrapers.run import run_scrapers
from scrapers.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def scraper_job():
    """Background job to run scrapers"""
    try:
        logger.info("Running scheduled scraper job...")
        run_scrapers()
        logger.info("Scraper job completed successfully")
    except Exception as e:
        logger.error(f"Error in scraper job: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global scheduler
    
    # Startup: Start the scheduler
    scheduler = AsyncIOScheduler()
    
    # Add scraper job (interval from settings, now set to 60 minutes)
    scheduler.add_job(
        scraper_job,
        'interval',
        minutes=settings.SCRAPER_INTERVAL_MINUTES,
        id='scraper_job',
        max_instances=1
    )
    
    scheduler.start()
    logger.info(f"✓ Background scheduler started - Scrapers run every {settings.SCRAPER_INTERVAL_MINUTES} minutes")
    
    yield
    
    # Shutdown: Stop the scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")

app = FastAPI(
    title="Telecom Outage API",
    description="API for accessing Swedish telecom outage data (Telia, Tre, Lycamobile)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = ["*"]

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(outages.router)
app.include_router(operators.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(regions.router, prefix="/api/v1")
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Telecom Outage API is running"}

@app.get("/api/v1/scheduler/status")
def scheduler_status():
    """Check scheduler status and next run times"""
    if not scheduler:
        return {"status": "disabled", "message": "Scheduler is not running"}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running",
        "jobs": jobs
    }
