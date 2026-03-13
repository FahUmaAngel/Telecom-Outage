import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import auto_resolve_expired_outages

def main():
    db = SessionLocal()
    try:
        print(f"[{datetime.now()}] Starting one-time auto-resolve run...")
        resolved_count = auto_resolve_expired_outages(db)
        print(f"[{datetime.now()}] Successfully resolved {resolved_count} expired outages.")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
