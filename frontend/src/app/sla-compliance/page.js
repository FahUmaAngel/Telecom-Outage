"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { ChevronDown, CheckCircle2, XCircle, AlertCircle, Download } from "lucide-react";
import { downloadCsv } from "../../lib/exportCsv";
import PropTypes from "prop-types";

const OPERATOR_COLORS = {
    telia: "#A31FD0",
    tre: "#EB6F2A",
    telenor: "#0070b8",
    lycamobile: "#22C55E",
};

const getOpColor = (name) =>
    OPERATOR_COLORS[(name || "").toLowerCase()] || "var(--accent-primary)";

const BENCHMARKS = ["ITU-T_E.800", "ETSI_EG_202_057-1", "PTSFS_2014:1"];

const BENCHMARK_LABELS = {
    "ITU-T_E.800": "ITU-T E.800",
    "ETSI_EG_202_057-1": "ETSI EG 202 057-1",
    "PTSFS_2014:1": "PTSFS 2014:1 (PTS)",
};

const BENCHMARK_DESC = {
    "ITU-T_E.800": "International: Critical ≤4h · Major ≤24h · Minor ≤72h",
    "ETSI_EG_202_057-1": "European: Critical ≤8h · Major ≤48h · Minor ≤120h",
    "PTSFS_2014:1": "Swedish PTS: Critical ≤1h · Major ≤24h · Minor ≤96h",
};

function OperatorCard({ r, lang }) {
    const rate = r.compliance_rate_pct.toFixed(1);
    const color = getOpColor(r.operator_name);
    const compliant = r.compliance_rate_pct >= 70;
    const sevEntries = Object.entries(r.by_severity || {});
    return (
        <div className="op-card">
            <div className="op-card-header">
                <span className="op-badge" style={{ background: color }}>{r.operator_name.toUpperCase()}</span>
                {compliant
                    ? <span className="badge-ok"><CheckCircle2 size={13} /> {lang === "sv" ? "Uppfyller" : "Compliant"}</span>
                    : <span className="badge-fail"><XCircle size={13} /> {lang === "sv" ? "Uppfyller ej" : "Non-compliant"}</span>
                }
            </div>
            <div className="compliance-bar-wrap">
                <div className="compliance-bar-track">
                    <div className="compliance-bar-fill" style={{ width: `${rate}%`, background: color }} />
                    <div className="threshold-line" />
                </div>
                <span className="compliance-pct">{rate}%</span>
            </div>
            <table className="severity-table">
                <thead>
                    <tr>
                        <th>{lang === "sv" ? "Allvarlighet" : "Severity"}</th>
                        <th>{lang === "sv" ? "Tröskel" : "Threshold"}</th>
                        <th>N</th>
                        <th>{lang === "sv" ? "Medel MTTR" : "Avg MTTR"}</th>
                        <th>%</th>
                    </tr>
                </thead>
                <tbody>
                    {sevEntries.map(([sevKey, sv]) => (
                        <tr key={sevKey}>
                            <td><span className={`sev-pill sev-${sevKey === "high" ? "critical" : sevKey === "medium" ? "major" : sevKey === "low" ? "minor" : "major"}`}>{sevKey}</span></td>
                            <td className="mono">≤{sv.threshold_hours}h</td>
                            <td className="mono">{sv.incidents}</td>
                            <td className="mono">{sv.actual_mean_hours?.toFixed(1)}h</td>
                            <td style={{ color: sv.compliance_pct >= 70 ? "var(--status-success)" : "var(--status-error)", fontWeight: 700 }}>
                                {sv.compliance_pct?.toFixed(0)}%
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className="op-meta">
                <span>N={r.total_incidents} {lang === "sv" ? "händelser" : "incidents"}</span>
                <span>{lang === "sv" ? "Uppfyllda" : "Compliant"}: {r.compliant_count} / {r.total_incidents}</span>
            </div>
        </div>
    );
}
OperatorCard.propTypes = {
    r: PropTypes.object.isRequired,
    lang: PropTypes.string.isRequired,
};

function ComparisonTable({ results, lang }) {
    return (
        <div className="table-card">
            <table className="stats-table">
                <thead>
                    <tr>
                        <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                        <th>{lang === "sv" ? "Efterlevnad" : "Compliance"}</th>
                        <th>{lang === "sv" ? "Händelser" : "Incidents"}</th>
                        <th>{lang === "sv" ? "Uppfyllda" : "Compliant"}</th>
                        <th>High</th><th>Medium</th><th>Low</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {[...results].sort((a, b) => b.compliance_rate_pct - a.compliance_rate_pct).map(r => {
                        const bySev = r.by_severity || {};
                        return (
                            <tr key={r.operator_name}>
                                <td><span className="op-badge" style={{ background: getOpColor(r.operator_name) }}>{r.operator_name.toUpperCase()}</span></td>
                                <td style={{ fontWeight: 700, color: r.compliance_rate_pct >= 70 ? "var(--status-success)" : "var(--status-error)" }}>
                                    {r.compliance_rate_pct.toFixed(1)}%
                                </td>
                                <td>{r.total_incidents}</td>
                                <td>{r.compliant_count} / {r.total_incidents}</td>
                                {["high", "medium", "low"].map(sev => (
                                    <td key={sev} className="mono">
                                        {bySev[sev] ? `${bySev[sev].compliance_pct?.toFixed(0)}%` : "—"}
                                    </td>
                                ))}
                                <td>
                                    {r.compliance_rate_pct >= 70
                                        ? <CheckCircle2 size={16} color="var(--status-success)" />
                                        : <XCircle size={16} color="var(--status-error)" />
                                    }
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
ComparisonTable.propTypes = {
    results: PropTypes.arrayOf(PropTypes.object).isRequired,
    lang: PropTypes.string.isRequired,
};

function PageFilters({ days, setDays, benchmark, setBenchmark, onExport, hasData, lang }) {
    return (
        <div className="filters-row">
            <div className="premium-filter">
                <label htmlFor="sla-period">PERIOD</label>
                <div className="select-wrapper">
                    <select id="sla-period" value={days} onChange={(e) => setDays(e.target.value)}>
                        <option value="30">30 {lang === "sv" ? "dagar" : "days"}</option>
                        <option value="90">90 {lang === "sv" ? "dagar" : "days"}</option>
                        <option value="180">180 {lang === "sv" ? "dagar" : "days"}</option>
                        <option value="365">365 {lang === "sv" ? "dagar" : "days"}</option>
                        <option value="730">730 {lang === "sv" ? "dagar" : "days"}</option>
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                </div>
            </div>
            <div className="premium-filter">
                <label htmlFor="sla-standard">STANDARD</label>
                <div className="select-wrapper">
                    <select id="sla-standard" value={benchmark} onChange={(e) => setBenchmark(e.target.value)}>
                        {BENCHMARKS.map(b => <option key={b} value={b}>{BENCHMARK_LABELS[b]}</option>)}
                    </select>
                    <ChevronDown size={14} className="select-icon" />
                </div>
            </div>
            <div className="premium-filter">
                <label>{lang === "sv" ? "EXPORTERA" : "EXPORT"}</label>
                <button className="export-btn" onClick={onExport} disabled={!hasData}>
                    <Download size={13} /> CSV
                </button>
            </div>
        </div>
    );
}
PageFilters.propTypes = {
    days: PropTypes.string.isRequired,
    setDays: PropTypes.func.isRequired,
    benchmark: PropTypes.string.isRequired,
    setBenchmark: PropTypes.func.isRequired,
    onExport: PropTypes.func.isRequired,
    hasData: PropTypes.bool.isRequired,
    lang: PropTypes.string.isRequired,
};

function ResultsPanel({ results, overallCompliance, benchmark, lang }) {
    return (
        <>
            <div className="kpi-row">
                <div className="kpi-card">
                    <span className="kpi-label">{lang === "sv" ? "Genomsnittlig efterlevnad" : "Avg Compliance"}</span>
                    <span className="kpi-value" style={{ color: Number(overallCompliance) >= 70 ? "var(--status-success)" : "var(--status-error)" }}>
                        {overallCompliance}%
                    </span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">Standard</span>
                    <span className="kpi-value kpi-value--sm">{BENCHMARK_LABELS[benchmark]}</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">{lang === "sv" ? "Operatörer" : "Operators"}</span>
                    <span className="kpi-value">{results.length}</span>
                </div>
            </div>
            <section className="section">
                <h2 className="section-title">{lang === "sv" ? "Efterlevnad per operatör" : "Compliance per Operator"}</h2>
                <div className="operator-grid">
                    {results.map(r => <OperatorCard key={r.operator_name} r={r} lang={lang} />)}
                </div>
            </section>
            <section className="section">
                <h2 className="section-title">{lang === "sv" ? "Jämförelsetabell" : "Comparison Table"}</h2>
                <ComparisonTable results={results} lang={lang} />
            </section>
        </>
    );
}
ResultsPanel.propTypes = {
    results: PropTypes.arrayOf(PropTypes.object).isRequired,
    overallCompliance: PropTypes.string,
    benchmark: PropTypes.string.isRequired,
    lang: PropTypes.string.isRequired,
};

function buildExportRows(results, benchmark, days) {
    return results.map(r => ({
        operator: r.operator_name,
        compliance_pct: r.compliance_rate_pct.toFixed(1),
        total_incidents: r.total_incidents,
        compliant_count: r.compliant_count,
        high_pct: r.by_severity?.high?.compliance_pct?.toFixed(0) ?? "",
        medium_pct: r.by_severity?.medium?.compliance_pct?.toFixed(0) ?? "",
        low_pct: r.by_severity?.low?.compliance_pct?.toFixed(0) ?? "",
        benchmark,
        days,
    }));
}

async function fetchSlaData(days, benchmark, setResults, setLoading) {
    setLoading(true);
    try {
        const data = await api.research.slaCompliance({ days: Number.parseInt(days), benchmark });
        setResults(Array.isArray(data) ? data : []);
    } catch (err) {
        console.error("SLA fetch failed:", err);
    } finally {
        setLoading(false);
    }
}

export default function SLACompliancePage() {
    const { lang } = useLanguage();
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState("365");
    const [benchmark, setBenchmark] = useState("ITU-T_E.800");

    const fetchData = useCallback(
        () => fetchSlaData(days, benchmark, setResults, setLoading),
        [days, benchmark]
    );

    useEffect(() => { fetchData(); }, [fetchData]);

    const handleExport = () => downloadCsv(
        `sla-compliance-${benchmark}-${days}d.csv`,
        buildExportRows(results, benchmark, days)
    );

    const overallCompliance = results.length > 0
        ? (results.reduce((s, r) => s + r.compliance_rate_pct, 0) / results.length).toFixed(1)
        : null;

    let mainContent;
    if (loading) {
        mainContent = <div className="loading-container"><div className="spinner" /></div>;
    } else if (results.length === 0) {
        mainContent = <div className="empty-state">{lang === "sv" ? "Ingen data tillgänglig." : "No data available."}</div>;
    } else {
        mainContent = <ResultsPanel results={results} overallCompliance={overallCompliance} benchmark={benchmark} lang={lang} />;
    }

    return (
        <div className="page-container animate-fade-in">
            <header className="page-header">
                <div>
                    <h1 className="text-gradient">
                        {lang === "sv" ? "SLA-efterlevnad" : "SLA Compliance"}
                    </h1>
                    <p className="subtitle">
                        {lang === "sv"
                            ? "Jämförelse mot internationella standarder — ITU-T E.800, ETSI, PTS"
                            : "Comparison against international standards — ITU-T E.800, ETSI, PTS"}
                    </p>
                </div>
                <PageFilters
                    days={days} setDays={setDays}
                    benchmark={benchmark} setBenchmark={setBenchmark}
                    onExport={handleExport} hasData={results.length > 0}
                    lang={lang}
                />
            </header>

            <div className="benchmark-banner">
                <AlertCircle size={14} />
                <span>{BENCHMARK_DESC[benchmark]}</span>
            </div>

            {mainContent}

            <style jsx global>{`
                .page-container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
                .page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; }
                .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; }
                .text-gradient { background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
                .filters-row { display: flex; gap: 16px; flex-wrap: wrap; }
                .premium-filter { display: flex; flex-direction: column; gap: 6px; }
                .premium-filter label { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.1em; color: var(--text-muted); }
                .select-wrapper { position: relative; }
                .select-wrapper select { appearance: none; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 8px 32px 8px 12px; font-size: 0.85rem; color: var(--text-primary); cursor: pointer; }
                .select-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-muted); }
                .benchmark-banner { display: flex; align-items: center; gap: 8px; background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 24px; }
                .kpi-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
                .kpi-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; display: flex; flex-direction: column; gap: 8px; }
                .kpi-label { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); }
                .kpi-value { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); font-family: monospace; }
                .kpi-value--sm { font-size: 1rem; font-family: inherit; }
                .section { margin-bottom: 40px; }
                .section-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; }
                .operator-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 16px; }
                .op-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; display: flex; flex-direction: column; gap: 14px; }
                .op-card-header { display: flex; align-items: center; gap: 12px; }
                .op-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; color: #fff; letter-spacing: 0.05em; }
                .badge-ok { display: flex; align-items: center; gap: 4px; padding: 3px 10px; background: rgba(34,197,94,0.1); color: var(--status-success); border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
                .badge-fail { display: flex; align-items: center; gap: 4px; padding: 3px 10px; background: rgba(239,68,68,0.1); color: var(--status-error); border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
                .compliance-bar-wrap { display: flex; align-items: center; gap: 12px; }
                .compliance-bar-track { flex: 1; height: 8px; background: var(--surface-hover); border-radius: 4px; position: relative; }
                .compliance-bar-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; }
                .threshold-line { position: absolute; left: 70%; top: -4px; bottom: -4px; width: 2px; background: var(--text-muted); opacity: 0.4; border-radius: 1px; }
                .compliance-pct { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); min-width: 44px; text-align: right; }
                .severity-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
                .severity-table th { padding: 6px 8px; text-align: left; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); border-bottom: 1px solid var(--border-color); }
                .severity-table td { padding: 6px 8px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); }
                .severity-table tr:last-child td { border-bottom: none; }
                .sev-pill { display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 0.7rem; font-weight: 700; }
                .sev-critical { background: rgba(239,68,68,0.12); color: var(--status-error); }
                .sev-major { background: rgba(245,158,11,0.12); color: var(--status-warning); }
                .sev-minor { background: rgba(99,102,241,0.1); color: var(--accent-primary); }
                .op-meta { display: flex; gap: 16px; font-size: 0.78rem; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 10px; }
                .table-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow-x: auto; }
                .stats-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
                .stats-table th { padding: 12px 16px; text-align: left; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border-color); }
                .stats-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); }
                .stats-table tr:last-child td { border-bottom: none; }
                .mono { font-family: monospace; }
                .loading-container { display: flex; justify-content: center; align-items: center; min-height: 300px; }
                .empty-state { text-align: center; color: var(--text-muted); padding: 60px 16px; font-size: 0.9rem; }
                .export-btn { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: 0.82rem; font-weight: 700; color: var(--text-secondary); cursor: pointer; }
                .export-btn:hover:not(:disabled) { border-color: var(--accent-primary); color: var(--accent-primary); }
                .export-btn:disabled { opacity: 0.4; cursor: not-allowed; }
                @media (max-width: 768px) {
                    .page-container { padding: 20px 16px; }
                    .page-header { flex-direction: column; gap: 12px; }
                    .filters-row { flex-wrap: wrap; gap: 10px; width: 100%; }
                    .premium-filter { width: 100%; }
                    .select-wrapper select { width: 100%; }
                    .export-btn { width: 100%; justify-content: center; }
                    .kpi-row { grid-template-columns: 1fr 1fr; }
                    .operator-grid { grid-template-columns: 1fr; }
                    .op-meta { flex-direction: column; gap: 4px; }
                    .benchmark-banner { font-size: 0.76rem; }
                }
                @media (max-width: 480px) {
                    .kpi-row { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
