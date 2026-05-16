"""
Pydantic schemas for research analytics endpoints (IEEE paper).

Kept separate from `backend/schemas.py` to make research-specific data
contracts easy to locate, version, and cite.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel


class PercentileStats(BaseModel):
    """Distribution percentiles for MTTR analysis.

    Used in /analytics/mttr-percentiles. Reports central tendency,
    dispersion (std_dev), and 95% confidence intervals computed via
    bootstrap resampling (n=1000) to support inferential claims in the
    research paper.
    """
    operator_name: str
    sample_size: int
    mean: float
    median: float          # P50
    p75: float
    p90: float
    p95: float
    p99: float
    std_dev: float
    min_value: float
    max_value: float
    ci_95_low: float       # 95% CI lower bound
    ci_95_high: float


class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int


class DistributionResponse(BaseModel):
    """Empirical MTTR distribution for a single operator."""
    operator_name: str
    sample_size: int
    bins: List[HistogramBin]
    distribution_fit: Optional[str] = None  # e.g. 'lognormal'


class SLAComplianceResult(BaseModel):
    """SLA pass/fail summary for a single operator + benchmark."""
    operator_name: str
    benchmark: str                   # e.g. 'ITU-T_E.800'
    total_incidents: int
    compliant_count: int
    non_compliant_count: int
    compliance_rate_pct: float
    by_severity: Dict[str, Dict[str, float]]


class ValueScoreComponent(BaseModel):
    metric: str
    raw_value: float
    normalized_score: float          # 0-100, higher = better
    weight: float
    weighted_score: float


class ValueScoreResult(BaseModel):
    """Composite Consumer Value Score (CVS) for an operator."""
    operator_name: str
    composite_score: float           # 0-100
    rank: int
    components: List[ValueScoreComponent]
    interpretation: str              # Excellent / Good / Fair / Poor


class StatisticalTestResult(BaseModel):
    """Result of a between-operator statistical comparison."""
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    interpretation: str
    sample_sizes: Dict[str, int]
    effect_size: Optional[float] = None
