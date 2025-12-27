"""
Scheduler for scrapers.
Runs run.py every X minutes.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from run import run_scrapers
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

def start_scheduler():
    scheduler = BlockingScheduler()
    
    # Add job
    scheduler.add_job(
        run_scrapers, 
        'interval', 
        minutes=settings.SCRAPER_INTERVAL_MINUTES,
        id='scraper_job'
    )
    
    logger.info(f"Scheduler started. Running every {settings.SCRAPER_INTERVAL_MINUTES} minutes.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    start_scheduler()
