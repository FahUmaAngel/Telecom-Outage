"""
Crowd Detection Engine: Analyzes user reports and 3rd party signals.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..db.models import UserReport, Region, Operator
from ..crowd.mock_aggregator import MockAggregator
from .translation import create_bilingual_text
from typing import List, Dict

# Thresholds for detection
REPORT_THRESHOLD = 5  # Min reports in a region to trigger an alert
TIME_WINDOW_MINUTES = 30

def detect_hotspots(db: Session) -> List[Dict]:
    """
    Cluster UserReport entries and identify hotspots.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=TIME_WINDOW_MINUTES)
    
    # Query pending reports within the time window
    reports = db.query(UserReport).filter(
        UserReport.created_at >= cutoff,
        UserReport.status == "pending"
    ).all()
    
    # Group by Operator + Region
    clusters = {}
    for r in reports:
        key = (r.operator_id, r.region_id)
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(r)
        
    hotspots = []
    for (op_id, region_id), group in clusters.items():
        if len(group) >= REPORT_THRESHOLD:
            region = db.query(Region).filter(Region.id == region_id).first()
            operator = db.query(Operator).filter(Operator.id == op_id).first()
            
            hotspots.append({
                "operator_name": operator.name if operator else "Unknown",
                "region_id": region_id,
                "region_name": region.name if region else create_bilingual_text("Everywhere"),
                "report_count": len(group),
                "type": "USER_CLUSTER",
                "detected_at": datetime.utcnow()
            })
            
    return hotspots

def aggregate_external_signals() -> List[Dict]:
    """
    Fetch signals from 3rd party aggregators.
    """
    # For now, just using the mock aggregator
    aggregator = MockAggregator()
    signals = aggregator.fetch_signals()
    
    results = []
    for s in signals:
        results.append({
            "operator_name": s.operator,
            "region_name": create_bilingual_text(s.region_name) if s.region_name else None,
            "report_count": s.count,
            "type": "EXTERNAL_SIGNAL",
            "source": s.source_name,
            "detected_at": s.detected_at
        })
    return results

def run_crowd_listener(db: Session):
    """
    Main entry point for the crowd detection process.
    """
    print(f"[{datetime.utcnow()}] Running Crowd Listener...")
    
    # 1. Detect hotspots from internal reports
    hotspots = detect_hotspots(db)
    for h in hotspots:
        print(f"HOTSPOT DETECTED: {h['operator_name']} in {h['region_name']} ({h['report_count']} reports)")
        
    # 2. Get external signals
    external = aggregate_external_signals()
    for e in external:
        print(f"EXTERNAL SIGNAL: {e['operator_name']} in {e['region_name']} ({e['report_count']} via {e['source']})")
        
    return hotspots + external
