"""
Standardize affected_services in the database.
KEEPS: 5g+, 5g, 4g, 3g, 2g
REMOVES: voice, data, sms, mms, fiber, broadband, mobile (legacy)
Re-classifies from title/description if needed.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.db.connection import SessionLocal
from scrapers.db.models import Outage
from scrapers.common.engine import classify_services

VALID_GENERATIONS = {"5g+", "5g", "4g", "3g", "2g"}

def standardize():
    db = SessionLocal()
    try:
        outages = db.query(Outage).all()
        print(f"Processing {len(outages)} outages...")

        updated_count = 0
        for o in outages:
            # Step 1: Filter existing services to only keep valid generations
            current = o.affected_services or []
            filtered = [s for s in current if str(s).lower() in VALID_GENERATIONS]

            # Step 2: If nothing remains after filtering, re-classify from text
            if not filtered:
                text = ""
                if o.title:
                    if isinstance(o.title, dict):
                        text += " ".join(o.title.values())
                    else:
                        text += str(o.title)
                if o.description:
                    if isinstance(o.description, dict):
                        text += " " + " ".join(o.description.values())
                    else:
                        text += " " + str(o.description)

                new_services = classify_services(text)
                filtered = sorted([s.value if hasattr(s, 'value') else s for s in new_services])

            # Step 3: Sort for a consistent format
            filtered = sorted(set(str(s).lower() for s in filtered if str(s).lower() in VALID_GENERATIONS))
            if not filtered:
                filtered = ["4g", "5g"]  # Hard fallback

            current_sorted = sorted(set(str(s).lower() for s in (o.affected_services or [])))
            if current_sorted != filtered:
                o.affected_services = filtered
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"  Updated {updated_count} so far...")

        db.commit()
        print(f"\nDone. Updated {updated_count} outages.")

        # Quick summary
        from collections import Counter
        all_services = []
        for o in db.query(Outage).all():
            all_services.extend(o.affected_services or [])
        counts = Counter(all_services)
        print("\nService distribution after cleanup:")
        for svc, count in sorted(counts.items()):
            print(f"  {svc:10s}: {count}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    standardize()
