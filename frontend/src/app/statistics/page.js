"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    Legend
} from "recharts";
import { ChevronDown, AlertCircle, CheckCircle2 } from "lucide-react";

const OPERATOR_COLORS = {
    telia: "#A31FD0",
    tre: "#EB6F2A",
    telenor: "#0070b8",
    lycamobile: "#22C55E",
};

const getOpColor = (name) => {
    const key = (name || "").toLowerCase();
    return OPERATOR_COLORS[key] || "var(--accent-primary)";
};
export default function StatisticsPage() {
    const { lang } = useLanguage();
    const [percentiles, setPercentiles] = useState([]);
    const [distribution, setDistribution] = useState([]);
    const [testResult, setTestResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState("365");
    const [testType, setTestType] = useState("kruskal");

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const params = { days: Number.parseInt(days) };
            const [pData, dData, tData] = await Promise.all([
                api.research.mttrPercentiles(params),
                api.research.mttrDistribution(params),
                api.research.statisticalTest({ ...params, test: testType }),
            ]);
            setPercentiles(pData || []);
            setDistribution(dData || []);
            setTestResult(tData);
        } catch (err) {
            console.error("Statistics fetch failed:", err);
        } finally {
            setLoading(false);
        }
    }, [days, testType]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    if (loading) {
        return <div className="loading-container"><div className="spinner"></div></div>;
    }

    const percentileChartData = percentiles
        .filter(p => p.sample_size > 0)
        .map(p => ({
            name: p.operator_name.toUpperCase(),
            P50: p.median,
            P75: p.p75,
            P90: p.p90,
            P95: p.p95,
            P99: p.p99,
            color: getOpColor(p.operator_name),
        }));

    return (
        <div className="stats-container animate-fade-in">
            <header className="page-header">
                <div>
                    <h1 className="text-gradient">
                        {lang === "sv" ? "Statistisk Analys" : "Statistical Analysis"}
                    </h1>
                    <p className="subtitle">
                        {lang === "sv"
                            ? "MTTR-distribution, percentiler och hypotesprovning"
                            : "MTTR distribution, percentiles, and hypothesis testing"}
                    </p>
                </div>
                <div className="filters-row">
                    <div className="premium-filter">
                        <label htmlFor="period">{lang === "sv" ? "PERIOD" : "PERIOD"}</label>
                        <div className="select-wrapper">
                            <select id="period" value={days} onChange={(e) => setDays(e.target.value)}>
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
                        <label htmlFor="test">{lang === "sv" ? "STATISTISKT TEST" : "STATISTICAL TEST"}</label>
                        <div className="select-wrapper">
                            <select id="test" value={testType} onChange={(e) => setTestType(e.target.value)}>
                                <option value="kruskal">Kruskal-Wallis H</option>
                                <option value="anova">One-way ANOVA</option>
                            </select>
                            <ChevronDown size={14} className="select-icon" />
                        </div>
                    </div>
                </div>
            </header>

            {/* Percentile Table */}
            {percentiles.filter(p => p.sample_size > 0).length > 0 && (
                <section className="stats-section">
                    <h2 className="section-title">
                        {lang === "sv" ? "MTTR-percentiler per operatör" : "MTTR Percentiles per Operator"}
                    </h2>
                    <div className="table-card">
                        <table className="stats-table">
                            <thead>
                                <tr>
                                    <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                                    <th>N</th>
                                    <th>P50</th>
                                    <th>P75</th>
                                    <th>P90</th>
                                    <th>P95</th>
                                    <th>P99</th>
                                    <th>{lang === "sv" ? "Medel" : "Mean"}</th>
                                    <th>95% CI</th>
                                </tr>
                            </thead>
                            <tbody>
                                {percentiles.filter(p => p.sample_size > 0).map(p => (
                                    <tr key={p.operator_name}>
                                        <td>
                                            <span className="op-badge" style={{ background: getOpColor(p.operator_name) }}>
                                                {p.operator_name.toUpperCase()}
                                            </span>
                                        </td>
                                        <td>{p.sample_size}</td>
                                        <td>{p.median}h</td>
                                        <td>{p.p75}h</td>
                                        <td>{p.p90}h</td>
                                        <td>{p.p95}h</td>
                                        <td>{p.p99}h</td>
                                        <td>{p.mean}h</td>
                                        <td className="ci-cell">[{p.ci_95_low}–{p.ci_95_high}]</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}

            {/* Percentile Bar Chart */}
            {percentileChartData.length > 0 && (
                <section className="stats-section">
                    <h2 className="section-title">
                        {lang === "sv" ? "Percentilfördelning (timmar)" : "Percentile Distribution (hours)"}
                    </h2>
                    <div className="chart-card">
                        <ResponsiveContainer width="100%" height={320}>
                            <BarChart data={percentileChartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                                <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 12 }} unit="h" />
                                <Tooltip
                                    contentStyle={{ background: "var(--surface-color)", border: "1px solid var(--border-color)", borderRadius: 8 }}
                                    formatter={(v) => `${v}h`}
                                />
                                <Legend />
                                <Bar dataKey="P50" name="P50" fill="#6366f1" radius={[3,3,0,0]} />
                                <Bar dataKey="P75" name="P75" fill="#8b5cf6" radius={[3,3,0,0]} />
                                <Bar dataKey="P90" name="P90" fill="#a855f7" radius={[3,3,0,0]} />
                                <Bar dataKey="P95" name="P95" fill="#ec4899" radius={[3,3,0,0]} />
                                <Bar dataKey="P99" name="P99" fill="#f43f5e" radius={[3,3,0,0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>
            )}

            {/* Distribution Histogram */}
            {distribution.filter(d => d.bins && d.bins.length > 0).length > 0 && (
                <section className="stats-section">
                    <h2 className="section-title">
                        {lang === "sv" ? "MTTR-distribution (histogram)" : "MTTR Distribution (histogram)"}
                    </h2>
                    <div className="dist-grid">
                        {distribution.filter(d => d.bins && d.bins.length > 0).map(d => {
                            const histData = d.bins.map(b => ({
                                label: `${b.bin_start}–${b.bin_end}`,
                                count: b.count,
                            }));
                            return (
                                <div key={d.operator_name} className="chart-card">
                                    <div className="chart-header">
                                        <span className="op-badge" style={{ background: getOpColor(d.operator_name) }}>
                                            {d.operator_name.toUpperCase()}
                                        </span>
                                        <span className="chart-meta">
                                            n={d.sample_size}
                                            {d.distribution_fit && ` · ${d.distribution_fit}`}
                                        </span>
                                    </div>
                                    <ResponsiveContainer width="100%" height={180}>
                                        <BarChart data={histData} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                            <XAxis dataKey="label" tick={{ fontSize: 9, fill: "var(--text-muted)" }} interval="preserveStartEnd" />
                                            <YAxis tick={{ fontSize: 10, fill: "var(--text-muted)" }} />
                                            <Tooltip
                                                contentStyle={{ background: "var(--surface-color)", border: "1px solid var(--border-color)", borderRadius: 8, fontSize: 12 }}
                                            />
                                            <Bar dataKey="count" fill={getOpColor(d.operator_name)} radius={[2,2,0,0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            );
                        })}
                    </div>
                </section>
            )}

            {/* Statistical Test Result */}
            {testResult && (
                <section className="stats-section">
                    <h2 className="section-title">
                        {lang === "sv" ? "Hypotesprovning" : "Hypothesis Testing"}
                    </h2>
                    <div className="test-card">
                        <div className="test-header">
                            <span className="test-name">{testResult.test_name}</span>
                            {testResult.significant
                                ? <span className="badge-sig"><CheckCircle2 size={14} /> {lang === "sv" ? "Signifikant" : "Significant"}</span>
                                : <span className="badge-nosig"><AlertCircle size={14} /> {lang === "sv" ? "Inte signifikant" : "Not Significant"}</span>
                            }
                        </div>
                        <div className="test-stats">
                            <div className="stat-item">
                                <span className="stat-label">{lang === "sv" ? "Teststatistik" : "Test Statistic"}</span>
                                <span className="stat-value">{testResult.statistic?.toFixed(4)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">p-värde</span>
                                <span className="stat-value" style={{ color: testResult.significant ? "var(--status-success)" : "var(--status-warning)" }}>
                                    {testResult.p_value < 0.001 ? "< 0.001" : testResult.p_value?.toFixed(4)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">{lang === "sv" ? "Effektstorlek (η²)" : "Effect Size (η²)"}</span>
                                <span className="stat-value">{testResult.effect_size != null ? testResult.effect_size.toFixed(4) : "—"}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">{lang === "sv" ? "Stickprov" : "Sample Sizes"}</span>
                                <span className="stat-value" style={{ fontSize: "0.85rem" }}>
                                    {testResult.sample_sizes && Object.entries(testResult.sample_sizes).map(([k,v]) => `${k.toUpperCase()}=${v}`).join(" · ")}
                                </span>
                            </div>
                        </div>
                        {testResult.interpretation && (
                            <p className="test-interpretation">{testResult.interpretation}</p>
                        )}
                    </div>
                </section>
            )}

            <style jsx>{`
                .stats-container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
                .page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 32px; }
                .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; }
                .filters-row { display: flex; gap: 16px; flex-wrap: wrap; }
                .premium-filter { display: flex; flex-direction: column; gap: 6px; }
                .premium-filter label { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.1em; color: var(--text-muted); }
                .select-wrapper { position: relative; }
                .select-wrapper select { appearance: none; background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 8px 32px 8px 12px; font-size: 0.85rem; color: var(--text-primary); cursor: pointer; }
                .select-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-muted); }
                .stats-section { margin-bottom: 36px; }
                .section-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; letter-spacing: 0.02em; }
                .table-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow-x: auto; }
                .stats-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
                .stats-table th { padding: 12px 16px; text-align: left; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border-color); }
                .stats-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-color); color: var(--text-secondary); }
                .stats-table tr:last-child td { border-bottom: none; }
                .ci-cell { font-size: 0.78rem; color: var(--text-muted); font-family: monospace; }
                .op-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; color: #fff; letter-spacing: 0.05em; }
                .chart-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; }
                .chart-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
                .chart-meta { font-size: 0.78rem; color: var(--text-muted); }
                .dist-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
                .test-card { background: var(--surface-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px; }
                .test-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
                .test-name { font-size: 1rem; font-weight: 700; color: var(--text-primary); }
                .badge-sig { display: flex; align-items: center; gap: 4px; padding: 4px 10px; background: rgba(34,197,94,0.1); color: var(--status-success); border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
                .badge-nosig { display: flex; align-items: center; gap: 4px; padding: 4px 10px; background: rgba(245,158,11,0.1); color: var(--status-warning); border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
                .test-stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
                .stat-item { display: flex; flex-direction: column; gap: 4px; }
                .stat-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); }
                .stat-value { font-size: 1rem; font-weight: 700; color: var(--text-primary); font-family: monospace; }
                .test-interpretation { margin-top: 16px; font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; border-top: 1px solid var(--border-color); padding-top: 16px; }
                .loading-container { display: flex; justify-content: center; align-items: center; min-height: 300px; }
                .text-gradient { background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
            `}</style>
        </div>
    );
}
