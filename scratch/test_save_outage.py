import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.db.connection import SessionLocal
from scrapers.db.crud import save_outage
from scrapers.common.models import NormalizedOutage, OperatorEnum, OutageStatus, SeverityLevel

db = SessionLocal()
try:
    test_outage = NormalizedOutage(
        operator=OperatorEnum.TRE,
        incident_id="TEST-SCHEDULED",
        title={"sv": "Test", "en": "Test"},
        status=OutageStatus.SCHEDULED,
        severity=SeverityLevel.LOW,
        location="Stockholm"
    )
    
    print("Attempting to save scheduled outage...")
    res = save_outage(db, test_outage, {"test": True})
    if res is None:
        print("✓ Successfully skipped scheduled outage (res is None)")
    else:
        print("✗ FAILED: Scheduled outage was saved!")
        
    test_active = NormalizedOutage(
        operator=OperatorEnum.TRE,
        incident_id="TEST-ACTIVE",
        title={"sv": "Test Active", "en": "Test Active"},
        status=OutageStatus.ACTIVE,
        severity=SeverityLevel.LOW,
        location="Stockholm"
    )
    print("Attempting to save active outage...")
    res2 = save_outage(db, test_active, {"test": True})
    if res2:
        print(f"✓ Successfully saved active outage (ID: {res2.incident_id})")
        db.commit()
    else:
        print("✗ FAILED: Active outage was skipped!")
        
finally:
    db.close()
