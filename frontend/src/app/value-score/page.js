"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { ChevronDown, Download } from "lucide-react";
import { downloadCsv } from "../../lib/exportCsv";
import PropTypes from "prop-types";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from "recharts";

const OPERATOR_COLORS = {
    telia: "#A31FD0",
    tre: "#EB6F2A",
    telenor: "#0070b8",
    lycamobile: "#22C55E",
};

const getOpColor = (name) =>
    OPERATOR_COLORS[(name || "").toLowerCase()] || "var(--accent-primary)";

const CVS_WEIGHT_LABELS = {
    mttr: { sv: "Återhämtningshastighet", en: "Recovery Speed", weight: "30%" },
    frequency: { sv: "Avbrottsfrekvens", en: "Outage Frequency", weight: "20%" },
    downtime: { sv: "Total driftstopp", en: "Total Downtime", weight: "20%" },
    service_coverage: { sv: "Tjänsttäckning", en: "Service Coverage", weight: "15%" },
    sla_compliance: { sv: "SLA-efterlevnad", en: "SLA Compliance", weight: "15%" },
};

const RANK_MEDALS = ["🥇", "🥈", "🥉", "4."];

const buildRadarData = (ranked, lang) =>
    Object.keys(CVS_WEIGHT_LABELS).map(key => {
        const label = lang === "sv" ? CVS_WEIGHT_LABELS[key].sv : CVS_WEIGHT_LABELS[key].en;
        const entry = { component: label };
        for (const s of ranked) {
            const comp = (s.components || []).find(c => c.metric === key);
            entry[s.operator_name] = comp ? Number(comp.normalized_score.toFixed(1)) : 0;
        }
        return entry;
    });

const buildBarData = (ranked) =>
    ranked.map(s => ({
        name: s.operator_name.toUpperCase(),
        CVS: Number(s.composite_score.toFixed(1)),
    }));

const CompCell = ({ compMap, metricKey }) => {
    const c = compMap[metricKey];
    if (!c) return <td className="mono">—</td>;
    return (
        <td className="mono">
            <div className="comp-cell">
                <span>{c.normalized_score.toFixed(0)}%</span>
                {c.raw_value != null && <span className="raw-val">{c.raw_value}</span>}
            </div>
        </td>
    );
};
CompCell.propTypes = {
    compMap: PropTypes.object.isRequired,
    metricKey: PropTypes.string.isRequired,
};

function RankingSection({ ranked, lang }) {
    return (
        <section className="section">
            <h2 className="section-title">{lang === "sv" ? "CVS-ranking" : "CVS Ranking"}</h2>
            <div className="rank-grid">
                {ranked.map((s, i) => {
                    const color = getOpColor(s.operator_name);
                    const pct = s.composite_score.toFixed(1);
                    return (
                        <div key={s.operator_name} className={`rank-card${i === 0 ? " rank-first" : ""}`}>
                            <div className="rank-medal">{RANK_MEDALS[i] || `${i + 1}.`}</div>
                            <div className="rank-op-badge" style={{ background: color }}>{s.operator_name.toUpperCase()}</div>
                            <div className="rank-score" style={{ color }}>{pct}<span className="rank-score-unit">/100</span></div>
                            <div className="rank-bar-track">
                                <div className="rank-bar-fill" style={{ width: `${pct}%`, background: color }} />
                            </div>
                            <div className="rank-meta">{s.interpretation}</div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}
RankingSection.propTypes = {
    ranked: PropTypes.arrayOf(PropTypes.object).isRequired,
    lang: PropTypes.string.isRequired,
};

function BreakdownTable({ ranked, lang }) {
    return (
        <section className="section">
            <h2 className="section-title">{lang === "sv" ? "Komponentnedbrytning" : "Component Breakdown"}</h2>
            <div className="table-card">
                <table className="stats-table">
                    <thead>
                        <tr>
                            <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                            <th>CVS</th>
                            {Object.entries(CVS_WEIGHT_LABELS).map(([k, v]) => (
                                <th key={k}>{lang === "sv" ? v.sv : v.en}<span className="weight-chip">{v.weight}</span></th>
                            ))}
                            <th>{lang === "sv" ? "Placering" : "Rank"}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ranked.map((s, i) => {
                            const compMap = Object.fromEntries((s.components || []).map(c => [c.metric, c]));
                            return (
                                <tr key={s.operator_name}>
                                    <td>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <span>{RANK_MEDALS[i]}</span>
                                            <span className="op-badge" style={{ background: getOpColor(s.operator_name) }}>{s.operator_name.toUpperCase()}</span>
                                        </div>
                                    </td>
                                    <td style={{ fontWeight: 800, color: getOpColor(s.operator_name), fontFamily: "monospace" }}>
                                        {s.composite_score.toFixed(1)}%
                                    </td>
                                    {Object.keys(CVS_WEIGHT_LABELS).map(k => (
                                        <CompCell key={k} compMap={compMap} metricKey={k} />
                                    ))}
                                    <td>#{s.rank}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
BreakdownTable.propTypes = {
    ranked: PropTypes.arrayOf(PropTypes.object).isRequired,
    lang: PropTypes.string.isRequired,
};

function VSFilters({ days, setDays, onExport, hasData, lang }) {
    return (
        <div className="filters-row">
            <div className="premium-filter">
                <label htmlFor="period-vs">PERIOD</label>
                <div className="select-wrapper">
                    <select id="period-vs" value={days} onChange={(e) => setDays(e.target.value)}>
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
                <label>{lang === "sv" ? "EXPORTERA" : "EXPORT"}</label>
                <button className="export-btn" onClick={onExport} disabled={!hasData}>
                    <Download size={13} /> CSV
                </button>
            </div>
        </div>
    );
}
VSFilters.propTypes = {
    days: PropTypes.string.isRequired,
    setDays: PropTypes.func.isRequired,
    onExport: PropTypes.func.isRequired,
    hasData: PropTypes.bool.isRequired,
    lang: PropTypes.string.isRequired,
};

async function fetchValueScoreData(days, setScores, setLoading) {
    setLoading(true);
    try {
        const data = await api.research.valueScore({ days: Number.parseInt(days) });
        setScores(Array.isArray(data) ? data : []);
    } catch (err) {
        console.error("ValueScore fetch failed:", err);
    } finally {
        setLoading(false);
    }
}

function buildVsExportRows(ranked, days) {
    return ranked.map((s, i) => {
        const compMap = Object.fromEntries((s.components || []).map(c => [c.metric, c]));
        return {
            rank: i + 1,
            operator: s.operator_name,
            cvs: s.composite_score.toFixed(2),
            mttr_score: compMap.mttr?.normalized_score?.toFixed(1) ?? "",
            frequency_score: compMap.frequency?.normalized_score?.toFixed(1) ?? "",
            downtime_score: compMap.downtime?.normalized_score?.toFixed(1) ?? "",
            coverage_score: compMap.service_coverage?.normalized_score?.toFixed(1) ?? "",
            sla_score: compMap.sla_compliance?.normalized_score?.toFixed(1) ?? "",
            days,
        };
    });
}

export default function ValueScorePage() {
    const { lang } = useLanguage();
    const [scores, setScores] = useState([]);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState("365");

    const fetchData = useCallback(
        () => fetchValueScoreData(days, setScores, setLoading),
        [days]
    );

    useEffect(() => { fetchData(); }, [fetchData]);

    const ranked = [...scores].sort((a, b) => b.composite_score - a.composite_score);
    const radarData = buildRadarData(ranked, lang);
    const barData = buildBarData(ranked);

    const handleExport = () => downloadCsv(`value-score-${days}d.csv`, buildVsExportRows(ranked, days));

    let pageContent;
    if (loading) {
        pageContent = <div className="loading-container"><div className="spinner" /></div>;
    } else if (scores.length === 0) {
        pageContent = <div className="empty-state">{lang === "sv" ? "Ingen data tillgänglig." : "No data available."}</div>;
    } else {
        pageContent = (
            <>
                <RankingSection ranked={ranked} lang={lang} />
                <section className="section">
                    <h2 className="section-title">{lang === "sv" ? "CVS-jämförelse" : "CVS Comparison"}</h2>
                    <div className="chart-card">
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={barData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                                <YAxis domain={[0, 100]} tick={{ fill: "var(--text-secondary)", fontSize: 12 }} unit="%" />
                                <Tooltip contentStyle={{ background: "var(--surface-color)", border: "1px solid var(--border-color)", borderRadius: 8 }} formatter={(v) => [`${v}%`, "CVS"]} />
                                <Bar dataKey="CVS" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} label={{ position: "top", fontSize: 11, fill: "var(--text-secondary)", formatter: (v) => `${v}%` }} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>
                {ranked.length > 1 && (
                    <section className="section">
                        <h2 className="section-title">{lang === "sv" ? "Komponentjämförelse (radar)" : "Component Comparison (radar)"}</h2>
                        <div className="chart-card">
                            <ResponsiveContainer width="100%" height={320}>
                                <RadarChart data={radarData}>
                                    <PolarGrid stroke="var(--border-color)" />
                                    <PolarAngleAxis dataKey="component" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                    <Tooltip contentStyle={{ background: "var(--surface-color)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 12 }} />
                                    {ranked.map(s => (
                                        <Radar key={s.operator_name} name={s.operator_name.toUpperCase()} dataKey={s.operator_name} stroke={getOpColor(s.operator_name)} fill={getOpColor(s.operator_name)} fillOpacity={0.08} strokeWidth={2} />
                                    ))}
                                    <Legend />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </section>
                )}
                <BreakdownTable ranked={ranked} lang={lang} />
            </>
        );
    }

    return (
        <div className="page-container animate-fade-in">
            <header className="page-header">
                <div>
                    <h1 className="text-gradient">
                        {lang === "sv" ? "Konsumentvärdespoäng" : "Consumer Value Score"}
                    </h1>
                    <p className="subtitle">
                        {lang === "sv"
                            ? "Sammansatt CVS-ranking baserad på MTTR, frekvens, driftstopp, täckning och SLA"
                            : "Composite CVS ranking based on MTTR, frequency, downtime, coverage, and SLA"}
                    </p>
                </div>
                <VSFilters days={days} setDays={setDays} onExport={handleExport} hasData={ranked.length > 0} lang={lang} />
            </header>
            <div className="methodology-note">
                <strong>CVS = </strong>
                {Object.entries(CVS_WEIGHT_LABELS).map(([k, v]) => (
                    <span key={k}>{v.weight} × {lang === "sv" ? v.sv : v.en}{" "}</span>
                ))}
                <span className="note-cite">— Soldani et al. (2006) · ITU-T G.1011 (2015)</span>
            </div>
            {pageContent}

            <style jsx global>{`
                .page-container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
                .page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; }
                .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; }
                .text-gradient { background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
                .filters-row { display: flex; gap: 16px; }
                .premium-filter { display: flex; flex-direction: column; gap: 6px; }
                .premium-filter label { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.1em; color: var(--text-muted); }
                .select-wrapper { position: relative; }
                .select-wrapper select { appearance: none; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 8px 32px 8px 12px; font-size: 0.85rem; color: var(--text-primary); cursor: pointer; }
                .select-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-muted); }
                .export-btn { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: 0.82rem; font-weight: 700; color: var(--text-secondary); cursor: pointer; }
                .export-btn:hover:not(:disabled) { border-color: var(--accent-primary); color: var(--accent-primary); }
                .export-btn:disabled { opacity: 0.4; cursor: not-allowed; }
                .methodology-note { background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.15); border-radius: 8px; padding: 12px 16px; font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 28px; line-height: 1.8; }
                .methodology-note strong { color: var(--text-primary); }
                .note-cite { color: var(--text-muted); font-size: 0.78rem; }
                .section { margin-bottom: 40px; }
                .section-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; }
                .rank-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
                .rank-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; display: flex; flex-direction: column; gap: 10px; }
                .rank-first { border-color: rgba(245,158,11,0.5); background: rgba(245,158,11,0.03); }
                .rank-medal { font-size: 1.4rem; }
                .rank-op-badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 800; color: #fff; letter-spacing: 0.05em; align-self: flex-start; }
                .rank-score { font-size: 2rem; font-weight: 900; font-family: monospace; line-height: 1; }
                .rank-score-unit { font-size: 0.85rem; font-weight: 500; color: var(--text-muted); margin-left: 2px; }
                .rank-bar-track { height: 6px; background: var(--surface-hover); border-radius: 3px; }
                .rank-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
                .rank-meta { font-size: 0.75rem; color: var(--text-muted); }
                .chart-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; }
                .op-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; color: #fff; letter-spacing: 0.05em; }
                .table-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow-x: auto; }
                .stats-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
                .stats-table th { padding: 12px 14px; text-align: left; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
                .stats-table td { padding: 12px 14px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); }
                .stats-table tr:last-child td { border-bottom: none; }
                .weight-chip { display: inline-block; margin-left: 4px; padding: 1px 5px; background: var(--surface-hover); border-radius: 4px; font-size: 0.6rem; font-weight: 600; text-transform: none; letter-spacing: 0; color: var(--text-muted); }
                .mono { font-family: monospace; }
                .comp-cell { display: flex; flex-direction: column; gap: 1px; }
                .raw-val { font-size: 0.72rem; color: var(--text-muted); }
                .loading-container { display: flex; justify-content: center; align-items: center; min-height: 300px; }
                .empty-state { text-align: center; color: var(--text-muted); padding: 60px 16px; font-size: 0.9rem; }
                @media (max-width: 768px) {
                    .page-container { padding: 20px 16px; }
                    .page-header { flex-direction: column; gap: 12px; }
                    .filters-row { flex-wrap: wrap; gap: 10px; width: 100%; }
                    .premium-filter { width: 100%; }
                    .select-wrapper select { width: 100%; }
                    .export-btn { width: 100%; justify-content: center; }
                    .rank-grid { grid-template-columns: 1fr 1fr; }
                    .rank-score { font-size: 1.5rem; }
                    .methodology-note { font-size: 0.78rem; }
                }
                @media (max-width: 480px) {
                    .rank-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
