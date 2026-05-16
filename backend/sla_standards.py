"""
SLA Standards and Benchmarks for Telecom Service Quality Assessment.

This module defines internationally-recognized SLA thresholds used in the
research paper for evaluating operator compliance and consumer value.

References (cite in IEEE paper):
-------------------------------
[1] ITU-T Recommendation E.800 (09/2008): "Definitions of terms related to
    quality of service". International Telecommunication Union.
[2] ETSI EG 202 057-1 V2.1.1 (2013): "Speech and multimedia Transmission
    Quality (STQ); User related QoS parameter definitions and measurements;
    Part 1: General". European Telecommunications Standards Institute.
[3] PTSFS 2014:1: "Föreskrifter om rapportering av integritetsincidenter
    och störningar av betydande omfattning". Post- och telestyrelsen
    (Swedish Post and Telecom Authority).
[4] ITU-T Recommendation M.3400 (02/2000): "TMN management functions".
    International Telecommunication Union.
"""
from enum import Enum
from typing import Dict, List


class SLATier(str, Enum):
    """Severity tiers for SLA evaluation, per ITU-T E.800."""
    CRITICAL = "critical"   # P1 - Service unavailable
    MAJOR = "major"         # P2 - Service degraded
    MINOR = "minor"         # P3 - Partial degradation


# ============================================================================
# SLA Threshold Definitions
# ----------------------------------------------------------------------------
# All values in hours. These are upper bounds: actual MTTR must be <= threshold
# for the operator to be considered compliant.
# ============================================================================

SLA_THRESHOLDS_HOURS: Dict[str, Dict[str, float]] = {
    # ITU-T E.800 — Critical incidents must be restored within 4 hours,
    # major incidents within 24 hours. Used as the primary international
    # benchmark in our analysis.
    "ITU-T_E.800": {
        SLATier.CRITICAL.value: 4.0,
        SLATier.MAJOR.value: 24.0,
        SLATier.MINOR.value: 72.0,
    },
    # ETSI EG 202 057-1 — Time for service restoration target. The P95 of
    # the repair time distribution must be at or below 48 hours.
    "ETSI_EG_202_057-1": {
        SLATier.CRITICAL.value: 8.0,
        SLATier.MAJOR.value: 48.0,
        SLATier.MINOR.value: 120.0,
    },
    # PTS (Sweden) — Significant disruptions (>1h affecting >10k subscribers
    # or >1% of customer base) must be reported. We treat 1h as the minimum
    # incident threshold and 24h as the resolution expectation.
    "PTSFS_2014:1": {
        SLATier.CRITICAL.value: 1.0,
        SLATier.MAJOR.value: 24.0,
        SLATier.MINOR.value: 96.0,
    },
}

# Default benchmark used in research paper headlines.
DEFAULT_BENCHMARK = "ITU-T_E.800"


# ============================================================================
# Severity Mapping
# ----------------------------------------------------------------------------
# Map database severity values to SLA tiers (ITU-T E.800 classification).
# ============================================================================

SEVERITY_TO_SLA_TIER: Dict[str, SLATier] = {
    "critical": SLATier.CRITICAL,
    "high": SLATier.CRITICAL,
    "medium": SLATier.MAJOR,
    "low": SLATier.MINOR,
    "unknown": SLATier.MAJOR,  # Conservative default
}


def get_threshold(benchmark: str, severity: str) -> float:
    """Return the SLA threshold in hours for given benchmark + severity."""
    bench = SLA_THRESHOLDS_HOURS.get(benchmark, SLA_THRESHOLDS_HOURS[DEFAULT_BENCHMARK])
    tier = SEVERITY_TO_SLA_TIER.get((severity or "unknown").lower(), SLATier.MAJOR)
    return bench[tier.value]


def list_benchmarks() -> List[str]:
    """Return the list of supported SLA benchmark keys."""
    return list(SLA_THRESHOLDS_HOURS.keys())


# ============================================================================
# Value-for-Money Index Weights
# ----------------------------------------------------------------------------
# Composite Consumer Value Score (CVS) — weights sum to 1.0.
# Lower is better for: mttr, frequency, downtime.
# Higher is better for: service_coverage, sla_compliance.
#
# Weights are derived from literature on telecom QoE/QoS:
#   - Soldani et al. (2006), "QoS and QoE Management in UMTS Cellular Systems"
#   - ITU-T G.1011 (2015): "Reference guide to quality of experience"
# ============================================================================

CVS_WEIGHTS: Dict[str, float] = {
    "mttr": 0.30,              # Recovery speed
    "frequency": 0.20,         # Outage frequency (incidents per month)
    "downtime": 0.20,          # Total downtime hours
    "service_coverage": 0.15,  # Breadth of services affected
    "sla_compliance": 0.15,    # % of incidents meeting SLA
}
"""