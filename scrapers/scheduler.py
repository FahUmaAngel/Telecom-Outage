"""
Scheduler for scrapers.
Runs run.py every X minutes.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from run import run_scrapers
from config import settings
import logging
from scrapers.db.connection import SessionLocal
from scrapers.db.crud import cleanup_old_data
from scrapers.common.crowd_engine import run_crowd_listener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

def daily_cleanup():
    db = SessionLocal()
    try:
        cleanup_old_data(db, days=30)
        logger.info("Daily cleanup job completed.")
    except Exception as e:
        logger.error(f"Error during daily cleanup: {e}")
    finally:
        db.close()

def run_crowd_job():
    db = SessionLocal()
    try:
        run_crowd_listener(db)
    finally:
        db.close()

def start_scheduler():
    scheduler = BlockingScheduler()
    
    # Add job for scrapers
    scheduler.add_job(
        run_scrapers, 
        'interval', 
        minutes=settings.SCRAPER_INTERVAL_MINUTES,
        id='scraper_job'
    )

    # Add crowd listener job
    scheduler.add_job(
        run_crowd_job,
        'interval',
        minutes=5,
        id='crowd_listener_job'
    )

    # Add daily cleanup job
    scheduler.add_job(
        daily_cleanup, 
        'cron', 
        hour=3, # Run daily at 3 AM
        id='daily_cleanup_job'
    )
    
    logger.info(f"Scheduler started. Scrapers running every {settings.SCRAPER_INTERVAL_MINUTES} minutes.")
    logger.info("Daily cleanup job scheduled for 3 AM.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    start_scheduler()
