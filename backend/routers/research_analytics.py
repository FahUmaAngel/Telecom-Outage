"""Research Analytics endpoints for IEEE Software paper.

Provides advanced statistical analysis of telecom outage MTTR data
to answer three research questions:
  RQ1: What is the MTTR distribution per operator?
  RQ2: Are consumers receiving value for their money?
  RQ3: Are operators meeting international SLA standards?

References:
  [1] ITU-T E.800 (2008) - QoS terms and definitions
  [2] ETSI EG 202 057-1 (2013) - User QoS parameters
  [3] PTSFS 2014:1 - Swedish telecom reporting regulations
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated, Tuple
from datetime import datetime, timedelta, timezone
import numpy as np
from scipy import stats as scistats

from ..dependencies import get_db
from ..schemas_research import (
    PercentileStats,
    DistributionResponse,
    HistogramBin,
    SLAComplianceResult,
    ValueScoreResult,
    ValueScoreComponent,
    StatisticalTestResult,
)
from ..sla_standards import (
    SLA_THRESHOLDS_HOURS,
    SEVERITY_TO_SLA_TIER,
    DEFAULT_BENCHMARK,
    CVS_WEIGHTS,
    get_threshold,
    list_benchmarks,
)
from scrapers.db.models import Outage, Operator

router = APIRouter(prefix="/api/v1/research", tags=["research"])

DAYS_MIN = 1
DAYS_MAX = 730
DEFAULT_DAYS = 365
BOOTSTRAP_ITERATIONS = 1000
RANDOM_SEED = 42
MTTR_SANITY_MAX_HOURS = 8760.0
HISTOGRAM_BINS = 20


def _clamp_days(days: int) -> int:
    return max(DAYS_MIN, min(days, DAYS_MAX))


def _strip_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt


def _calculate_mttr_hours(outage) -> Optional[float]:
    if not outage.start_time or not outage.end_time:
        return None
    st = _strip_tz(outage.start_time)
    et = _strip_tz(outage.end_time)
    duration_hours = (et - st).total_seconds() / 3600.0
    if 0 < duration_hours <= MTTR_SANITY_MAX_HOURS:
        return duration_hours
    return None


def _fetch_operator_mttrs(db, operator_id, since):
    outages = db.query(Outage).filter(
        Outage.operator_id == operator_id,
        Outage.start_time.isnot(None),
        Outage.end_time.isnot(None),
        Outage.start_time >= since,
    ).all()
    result = []
    for o in outages:
        m = _calculate_mttr_hours(o)
        if m is not None:
            result.append(m)
    return result


def _bootstrap_ci(values, confidence=0.95):
    if len(values) < 2:
        return (0.0, 0.0)
    rng = np.random.default_rng(RANDOM_SEED)
    arr = np.array(values)
    means = [rng.choice(arr, size=len(arr), replace=True).mean()
             for _ in range(BOOTSTRAP_ITERATIONS)]
    alpha = (1 - confidence) / 2
    low = float(np.percentile(means, alpha * 100))
    high = float(np.percentile(means, (1 - alpha) * 100))
    return (low, high)


def _normalize_score(value, best, worst, lower_is_better=True):
    if worst == best:
        return 100.0
    if lower_is_better:
        score = (worst - value) / (worst - best) * 100
    else:
        score = (value - worst) / (best - worst) * 100
    return float(max(0.0, min(100.0, score)))


def _interpret_score(score):
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


@router.get("/benchmarks", response_model=List[str])
def get_benchmarks():
    """List supported SLA benchmark identifiers."""
    return list_benchmarks()


@router.get("/mttr-percentiles", response_model=List[PercentileStats])
def get_mttr_percentiles(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=DEFAULT_DAYS, ge=DAYS_MIN, le=DAYS_MAX),
):
    """RQ1: Return distribution percentiles for MTTR per operator."""
    safe_days = _clamp_days(days)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    operators = db.query(Operator).all()
    results = []
    for op in operators:
        if op.name and op.name.lower() == "tele2":
            continue
        mttrs = _fetch_operator_mttrs(db, op.id, since)
        if not mttrs:
            results.append(PercentileStats(
                operator_name=op.name, sample_size=0,
                mean=0.0, median=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0,
                std_dev=0.0, min_value=0.0, max_value=0.0,
                ci_95_low=0.0, ci_95_high=0.0,
            ))
            continue
        arr = np.array(mttrs)
        ci_low, ci_high = _bootstrap_ci(mttrs)
        results.append(PercentileStats(
            operator_name=op.name,
            sample_size=len(mttrs),
            mean=round(float(arr.mean()), 2),
            median=round(float(np.percentile(arr, 50)), 2),
            p75=round(float(np.percentile(arr, 75)), 2),
            p90=round(float(np.percentile(arr, 90)), 2),
            p95=round(float(np.percentile(arr, 95)), 2),
            p99=round(float(np.percentile(arr, 99)), 2),
            std_dev=round(float(arr.std(ddof=1)) if len(arr) > 1 else 0.0, 2),
            min_value=round(float(arr.min()), 2),
            max_value=round(float(arr.max()), 2),
            ci_95_low=round(ci_low, 2),
            ci_95_high=round(ci_high, 2),
        ))
    return results

@router.get("/mttr-distribution", response_model=List[DistributionResponse])
def get_mttr_distribution(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=DEFAULT_DAYS, ge=DAYS_MIN, le=DAYS_MAX),
    bins: int = Query(default=HISTOGRAM_BINS, ge=5, le=50),
):
    """RQ1: Histogram bins of MTTR for visualization."""
    safe_days = _clamp_days(days)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    operators = db.query(Operator).all()
    results = []
    for op in operators:
        if op.name and op.name.lower() == "tele2":
            continue
        mttrs = _fetch_operator_mttrs(db, op.id, since)
        if len(mttrs) < 5:
            results.append(DistributionResponse(
                operator_name=op.name, sample_size=len(mttrs), bins=[],
                distribution_fit=None,
            ))
            continue
        arr = np.array(mttrs)
        counts, edges = np.histogram(arr, bins=bins)
        hist_bins = [
            HistogramBin(
                bin_start=round(float(edges[i]), 2),
                bin_end=round(float(edges[i+1]), 2),
                count=int(counts[i]),
            )
            for i in range(len(counts))
        ]
        fit_label = None
        try:
            arr_pos = arr[arr > 0]
            if len(arr_pos) >= 10:
                ln_params = scistats.lognorm.fit(arr_pos, floc=0)
                ln_ll = float(scistats.lognorm.logpdf(arr_pos, *ln_params).sum())
                ex_params = scistats.expon.fit(arr_pos, floc=0)
                ex_ll = float(scistats.expon.logpdf(arr_pos, *ex_params).sum())
                fit_label = "lognormal" if ln_ll > ex_ll else "exponential"
        except Exception:
            fit_label = None
        results.append(DistributionResponse(
            operator_name=op.name,
            sample_size=len(mttrs),
            bins=hist_bins,
            distribution_fit=fit_label,
        ))
    return results


@router.get("/sla-compliance", response_model=List[SLAComplianceResult])
def get_sla_compliance(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=DEFAULT_DAYS, ge=DAYS_MIN, le=DAYS_MAX),
    benchmark: str = Query(default=DEFAULT_BENCHMARK),
):
    """RQ3: Compare operators against international SLA benchmarks."""
    if benchmark not in SLA_THRESHOLDS_HOURS:
        benchmark = DEFAULT_BENCHMARK
    safe_days = _clamp_days(days)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    operators = db.query(Operator).all()
    results = []
    for op in operators:
        if op.name and op.name.lower() == "tele2":
            continue
        outages = db.query(Outage).filter(
            Outage.operator_id == op.id,
            Outage.start_time.isnot(None),
            Outage.end_time.isnot(None),
            Outage.start_time >= since,
        ).all()
        total = 0
        compliant = 0
        by_sev = {}
        for o in outages:
            mttr = _calculate_mttr_hours(o)
            if mttr is None:
                continue
            severity = (o.severity or "unknown").lower()
            threshold = get_threshold(benchmark, severity)
            is_compliant = mttr <= threshold
            total += 1
            if is_compliant:
                compliant += 1
            if severity not in by_sev:
                by_sev[severity] = {"threshold": threshold, "actual_mttrs": [], "compliant": 0, "total": 0}
            by_sev[severity]["actual_mttrs"].append(mttr)
            by_sev[severity]["total"] += 1
            if is_compliant:
                by_sev[severity]["compliant"] += 1
        by_severity_out = {}
        for sev, d in by_sev.items():
            mean_actual = float(np.mean(d["actual_mttrs"])) if d["actual_mttrs"] else 0.0
            rate = (d["compliant"] / d["total"] * 100) if d["total"] > 0 else 0.0
            by_severity_out[sev] = {
                "threshold_hours": round(d["threshold"], 2),
                "actual_mean_hours": round(mean_actual, 2),
                "compliance_pct": round(rate, 2),
                "incidents": float(d["total"]),
            }
        rate_total = (compliant / total * 100) if total > 0 else 0.0
        results.append(SLAComplianceResult(
            operator_name=op.name,
            benchmark=benchmark,
            total_incidents=total,
            compliant_count=compliant,
            non_compliant_count=total - compliant,
            compliance_rate_pct=round(rate_total, 2),
            by_severity=by_severity_out,
        ))
    return results


def _calculate_operator_metrics(db, op, since, safe_days):
    """Compute raw metrics for one operator (helper for value-score)."""
    outages = db.query(Outage).filter(
        Outage.operator_id == op.id,
        Outage.start_time.isnot(None),
        Outage.end_time.isnot(None),
        Outage.start_time >= since,
    ).all()
    mttrs = []
    services_set = set()
    sla_compliant = 0
    sla_total = 0
    for o in outages:
        m = _calculate_mttr_hours(o)
        if m is None:
            continue
        mttrs.append(m)
        if o.affected_services:
            for svc in o.affected_services:
                services_set.add(str(svc).lower())
        threshold = get_threshold(DEFAULT_BENCHMARK, (o.severity or "unknown").lower())
        sla_total += 1
        if m <= threshold:
            sla_compliant += 1
    months = max(safe_days / 30.0, 0.1)
    return {
        "mean_mttr": float(np.mean(mttrs)) if mttrs else 0.0,
        "frequency": len(mttrs) / months,
        "total_downtime": float(sum(mttrs)),
        "service_coverage": len(services_set),
        "sla_compliance": (sla_compliant / sla_total * 100) if sla_total > 0 else 0.0,
        "sample_size": len(mttrs),
    }


@router.get("/value-score", response_model=List[ValueScoreResult])
def get_value_score(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=DEFAULT_DAYS, ge=DAYS_MIN, le=DAYS_MAX),
):
    """RQ2: Composite Consumer Value Score (CVS) per operator.

    Weighted index across MTTR, frequency, downtime, service coverage,
    and SLA compliance. Operators are normalized relative to the best
    and worst observed within the period (min-max scaling) then weighted
    per CVS_WEIGHTS to yield a 0-100 score.
    """
    safe_days = _clamp_days(days)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    operators = [op for op in db.query(Operator).all()
                 if not (op.name and op.name.lower() == "tele2")]
    raw = {op.name: _calculate_operator_metrics(db, op, since, safe_days) for op in operators}
    if not raw:
        return []
    # Determine best/worst per metric for normalization
    def _bw(key, lower_is_better):
        vals = [m[key] for m in raw.values() if m["sample_size"] > 0]
        if not vals:
            return (0.0, 0.0)
        return (min(vals), max(vals)) if lower_is_better else (max(vals), min(vals))
    bw = {
        "mttr": _bw("mean_mttr", True),
        "frequency": _bw("frequency", True),
        "downtime": _bw("total_downtime", True),
        "service_coverage": _bw("service_coverage", False),
        "sla_compliance": _bw("sla_compliance", False),
    }
    scored = []
    for op_name, m in raw.items():
        if m["sample_size"] == 0:
            scored.append(ValueScoreResult(
                operator_name=op_name, composite_score=0.0, rank=0,
                components=[], interpretation="Insufficient data",
            ))
            continue
        components = []
        composite = 0.0
        mappings = [
            ("mttr", "mean_mttr", True),
            ("frequency", "frequency", True),
            ("downtime", "total_downtime", True),
            ("service_coverage", "service_coverage", False),
            ("sla_compliance", "sla_compliance", False),
        ]
        for weight_key, raw_key, lower_better in mappings:
            best, worst = bw[weight_key]
            norm = _normalize_score(m[raw_key], best, worst, lower_better)
            w = CVS_WEIGHTS[weight_key]
            weighted = norm * w
            composite += weighted
            components.append(ValueScoreComponent(
                metric=weight_key,
                raw_value=round(m[raw_key], 2),
                normalized_score=round(norm, 2),
                weight=w,
                weighted_score=round(weighted, 2),
            ))
        scored.append(ValueScoreResult(
            operator_name=op_name,
            composite_score=round(composite, 2),
            rank=0,
            components=components,
            interpretation=_interpret_score(composite),
        ))
    # Assign ranks (1 = best)
    scored.sort(key=lambda r: r.composite_score, reverse=True)
    for i, r in enumerate(scored):
        r.rank = i + 1
    return scored


@router.get("/statistical-test", response_model=StatisticalTestResult)
def get_statistical_test(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=DEFAULT_DAYS, ge=DAYS_MIN, le=DAYS_MAX),
    test: str = Query(default="kruskal", pattern="^(kruskal|anova)$"),
):
    """Non-parametric (Kruskal-Wallis H) or parametric (one-way ANOVA)
    test for differences in MTTR between operators.

    Default is Kruskal-Wallis because MTTR distributions are typically
    skewed (log-normal) and ANOVA assumptions of normality are violated.
    Effect size reported as eta-squared (eta^2).
    """
    safe_days = _clamp_days(days)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=safe_days)
    operators = db.query(Operator).all()
    groups = []
    labels = []
    sample_sizes = {}
    for op in operators:
        if op.name and op.name.lower() == "tele2":
            continue
        mttrs = _fetch_operator_mttrs(db, op.id, since)
        if len(mttrs) >= 5:
            groups.append(mttrs)
            labels.append(op.name)
            sample_sizes[op.name] = len(mttrs)
    if len(groups) < 2:
        return StatisticalTestResult(
            test_name=test,
            statistic=0.0, p_value=1.0, significant=False,
            interpretation="Insufficient operators with data (need >=2).",
            sample_sizes=sample_sizes, effect_size=None,
        )
    if test == "anova":
        stat, p = scistats.f_oneway(*groups)
        test_name = "One-way ANOVA (F-test)"
    else:
        stat, p = scistats.kruskal(*groups)
        test_name = "Kruskal-Wallis H test"
    # Eta-squared effect size: H / (n - 1) for Kruskal; SS_between/SS_total for ANOVA
    total_n = sum(len(g) for g in groups)
    if test == "kruskal":
        eta_sq = float(stat / (total_n - 1)) if total_n > 1 else None
    else:
        grand_mean = float(np.mean([v for g in groups for v in g]))
        ss_between = sum(len(g) * (float(np.mean(g)) - grand_mean) ** 2 for g in groups)
        ss_total = sum((v - grand_mean) ** 2 for g in groups for v in g)
        eta_sq = float(ss_between / ss_total) if ss_total > 0 else None
    sig = bool(p < 0.05)
    if sig:
        interp = (
            f"Significant difference in MTTR between operators (p={p:.4f} < 0.05). "
            f"Reject H0: at least one operator's distribution differs."
        )
    else:
        interp = (
            f"No significant difference detected (p={p:.4f} >= 0.05). "
            f"Fail to reject H0: MTTR distributions are statistically similar."
        )
    return StatisticalTestResult(
        test_name=test_name,
        statistic=round(float(stat), 4),
        p_value=round(float(p), 6),
        significant=sig,
        interpretation=interp,
        sample_sizes=sample_sizes,
        effect_size=round(eta_sq, 4) if eta_sq is not None else None,
    )
