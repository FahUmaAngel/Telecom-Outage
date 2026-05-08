"""
FastAPI Entry Point with Background Scheduler.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import outages, operators, reports, analytics, auth, regions, admin
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys
import os
import logging

# Add project root to path for scraper imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scrapers.run import run_scrapers
from scrapers.config import settings
from scrapers.db.connection import SessionLocal
from scrapers.db.models import User
from .auth import get_password_hash
from .websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def _parse_allowed_origins() -> list[str]:
    raw = getattr(settings, "ALLOWED_ORIGINS", None)
    if raw:
        return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]

    app_env = (getattr(settings, "APP_ENV", "development") or "development").lower()
    if app_env == "production":
        return []

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


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


async def scraper_job():
    """Background job to run scrapers"""
    try:
        logger.info("Running scheduled scraper job...")

        # 1. Run Scrapers
        run_scrapers()

        # Note: Auto-resolve based on ETA was removed to prevent status flapping.
        # Resolution is now handled entirely by Delta-Resolve (vanished incidents)
        # or explicitly by the scrapers.

        logger.info("Scraper job completed successfully. Broadcasting update...")
        await manager.broadcast({
            "type": "OUTAGE_UPDATE",
            "timestamp": datetime.now().isoformat(),
            "message": "New outage data available"
        })
    except Exception as e:
        logger.error(f"Error in scraper job: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global scheduler

    ensure_default_admin()

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

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt received")
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# CORS Configuration
origins = _parse_allowed_origins()

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Telecom Outage API is running"}


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
