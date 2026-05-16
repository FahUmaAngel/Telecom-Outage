"""
FastAPI Entry Point with Background Scheduler.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .routers import outages, operators, reports, analytics, auth, regions, admin, research_analytics
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys
import os
import logging

# Add project root to path for scraper imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scrapers.config import settings
from scrapers.db.connection import SessionLocal
from scrapers.db.crud import auto_resolve_expired_outages
from scrapers.db.models import User
from .auth import get_password_hash

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def ensure_default_admin():
    """Bootstrap a local admin user when the database has no users yet."""
    app_env = (getattr(settings, "APP_ENV", "development") or "development").lower()
    if app_env == "production":
        return

    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if existing_user:
            return

        username = getattr(settings, "ADMIN_USERNAME", None) or "admin"
        # We use a fallback ONLY in development if not provided via environment/settings
        password = getattr(settings, "ADMIN_PASSWORD", None) or os.environ.get("DEFAULT_ADMIN_PASSWORD")
        if not password:
            logger.warning("Default admin password not set. Skipping admin creation.")
            return

        db.add(User(
            username=username,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
        ))
        db.commit()
        logger.info("Created default development admin user '%s'", username)
    finally:
        db.close()

def scraper_job():
    """Background job to run scrapers"""
    try:
        logger.info("Running scheduled scraper job...")
        
        # 1. Run Scrapers (lazy import so API can start without scraper deps)
        from scrapers.run import run_scrapers
        run_scrapers()
        
        # 2. Auto-resolve expired outages
        db = SessionLocal()
        try:
            resolved_count = auto_resolve_expired_outages(db)
            if resolved_count > 0:
                logger.info(f"Auto-resolved {resolved_count} expired outages")
        finally:
            db.close()
            
        logger.info("Scraper job completed successfully")
    except Exception as e:
        logger.exception("Error in scraper job")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global scheduler

    ensure_default_admin()
    
    if getattr(settings, "ENABLE_SCHEDULER", True):
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
    else:
        logger.info("Background scheduler disabled (ENABLE_SCHEDULER=false)")
    
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
allowed_origins_str = getattr(settings, "ALLOWED_ORIGINS", None) or (
    "https://localhost:3000,https://127.0.0.1:3000,https://localhost:8080,https://127.0.0.1:8080"
)
origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(outages.router)
app.include_router(operators.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(regions.router, prefix="/api/v1")
app.include_router(admin.router)
app.include_router(research_analytics.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Telecom Outage API is running"}

# Optional: serve exported frontend (Next.js output: export) when present.
# This allows deploying backend + frontend together as a single service.
_frontend_out = os.path.join(os.path.dirname(__file__), "..", "frontend", "out")
if os.path.isdir(_frontend_out):
    app.mount("/", StaticFiles(directory=_frontend_out, html=True), name="frontend")

    @app.get("/{full_path:path}", include_in_schema=False)
    def _frontend_fallback(full_path: str):
        # Let API routes be handled by routers, not the static site.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_path = os.path.join(_frontend_out, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Not found")

@app.get("/api/v1/scheduler/status")
def scheduler_status():
    """Check scheduler status and next run times"""
    if not scheduler or not scheduler.running:
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
