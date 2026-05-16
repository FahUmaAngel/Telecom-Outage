import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.db.models import Base, Operator, Outage
from scrapers.db.crud import save_outage, mark_missing_outages_resolved, mark_stale_active_incidents
from backend.routers.analytics import _calculate_avg_mttr
from scrapers.common.models import NormalizedOutage, OperatorEnum

class TestLifecycle(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        
        # Add operator
        op = Operator(name="Telia")
        self.db.add(op)
        self.db.commit()
        
        self.now = datetime.now(timezone.utc)
        
    def tearDown(self):
        self.db.close()
        
    def test_missing_count_and_resolved_by_absence(self):
        # 1. Create active outage
        norm = NormalizedOutage(
            incident_id="T1",
            operator=OperatorEnum.TELIA,
            title={"sv": "Test", "en": "Test"},
            status="active",
            location="Stockholm",
            started_at=self.now - timedelta(days=16)
        )
        outage = save_outage(self.db, norm, {})
        self.assertEqual(outage.status, "active")
        self.assertEqual(outage.missing_count, 0)
        
        # 2. Scrape again, but outage is missing (so missing_count = 1)
        # Note: Since it was created 16 days ago, `last_seen_at` is set to now by `save_outage` initially.
        # Let's fake `last_seen_at` to be 16 days ago to test the 15-day rule.
        outage.last_seen_at = self.now - timedelta(days=16)
        self.db.commit()
        
        resolved_count = mark_missing_outages_resolved(self.db, "Telia", ["T2", "T3"])
        
        # Because it's missing for > 15 days, it should be marked as resolved_by_absence immediately
        self.assertEqual(resolved_count, 1)
        self.assertEqual(outage.status, "resolved")
        self.assertEqual(outage.resolution_type, "resolved_by_absence")
        
    def test_missing_count_no_resolve_early(self):
        norm = NormalizedOutage(
            incident_id="T2",
            operator=OperatorEnum.TELIA,
            title={"sv": "Test2", "en": "Test2"},
            status="active"
        )
        outage = save_outage(self.db, norm, {})
        # Fake last seen to 2 days ago
        outage.last_seen_at = self.now - timedelta(days=2)
        outage.missing_count = 3
        self.db.commit()
        
        # Mark missing
        resolved_count = mark_missing_outages_resolved(self.db, "Telia", ["T9"])
        self.assertEqual(resolved_count, 0)
        self.assertEqual(outage.status, "active")
        self.assertEqual(outage.missing_count, 4)
        
    def test_mark_stale(self):
        norm = NormalizedOutage(
            incident_id="T3",
            operator=OperatorEnum.TELIA,
            title={"sv": "Test3", "en": "Test3"},
            status="active"
        )
        outage = save_outage(self.db, norm, {})
        # Fake first seen to 31 days ago
        outage.first_seen_at = self.now - timedelta(days=31)
        self.db.commit()
        
        count = mark_stale_active_incidents(self.db, threshold_days=30)
        self.assertEqual(count, 1)
        self.assertTrue(outage.is_stale)
        self.assertEqual(outage.stale_reason, "Active for > 30 days")
        
    def test_mttr_calculation_excludes_absence_and_stale(self):
        # Official resolved (2 hours)
        o1 = Outage(
            operator_id=1, status='resolved', resolution_type='official_resolved',
            start_time=self.now - timedelta(hours=2), end_time=self.now
        )
        # Resolved by absence (5 hours)
        o2 = Outage(
            operator_id=1, status='resolved', resolution_type='resolved_by_absence',
            start_time=self.now - timedelta(hours=5), end_time=self.now
        )
        # Active
        o3 = Outage(operator_id=1, status='active', start_time=self.now - timedelta(hours=1))
        
        self.db.add_all([o1, o2, o3])
        self.db.commit()
        
        # Backend gets official outages
        official_outages = [o for o in [o1, o2, o3] if o.status == 'resolved' and o.resolution_type == 'official_resolved']
        
        self.assertEqual(len(official_outages), 1)
        self.assertEqual(official_outages[0], o1)
        
        mttr = _calculate_avg_mttr(official_outages)
        self.assertAlmostEqual(mttr, 2.0)
        
if __name__ == '__main__':
    unittest.main()
