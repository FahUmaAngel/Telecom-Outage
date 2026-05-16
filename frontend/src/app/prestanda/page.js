"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { ChevronDown, TrendingDown, Clock, AlertTriangle, CheckCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from "recharts";

export default function PrestandaPage() {
    const { lang } = useLanguage();
    const [mttrData, setMttrData] = useState([]);
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filters state
    const [period, setPeriod] = useState("365");
    const [town, setTown] = useState("");
    const [service, setService] = useState("");

    const fetchMTTR = useCallback(async () => {
        setLoading(true);
        try {
            const params = { days: Number.parseInt(period) };
            if (town) params.location = town;
            if (service) params.service = service;

            const results = await api.outages.mttrDynamic(params);
            setMttrData(results);
        } catch (err) {
            console.error("Failed to fetch MTTR data:", err);
        } finally {
            setLoading(false);
        }
    }, [period, town, service]);

    const fetchLocations = useCallback(async () => {
        try {
            const data = await api.outages.locations();
            setLocations(data);
        } catch (err) {
            console.error("Failed to fetch locations:", err);
        }
    }, []);

    useEffect(() => {
        fetchLocations();
    }, [fetchLocations]);

    useEffect(() => {
        fetchMTTR();
    }, [fetchMTTR]);

    const getOperatorColor = (name) => {
        const n = name.toLowerCase();
                if (n.includes('telia')) return '#A31FD0'; // Purple
        if (n.includes('tre')) return '#EB6F2A';   // Orange
        if (n.includes('telenor')) return '#0070b8'; // Telenor Blue
        if (n.includes('lyca')) return '#22C55E';  // Green
        return 'var(--accent-primary)';
    };

    // Derived stats
    const bestOperator = mttrData.length > 0
        ? mttrData.reduce((a, b) => (a.average_mttr_hours <= b.average_mttr_hours ? a : b))
        : null;
    const totalOutages = mttrData.reduce((s, d) => s + (d.outage_count || 0), 0);
    const avgAll = mttrData.length > 0
        ? (mttrData.reduce((s, d) => s + (d.average_mttr_hours || 0), 0) / mttrData.length).toFixed(1)
        : null;

    let gridContent;
    if (mttrData.length > 0) {
        gridContent = mttrData.map((data) => (
            <div key={data.operator_name} className="premium-card mttr-card" style={{ '--op-color': getOperatorColor(data.operator_name) }}>
                <div className="card-top-accent"></div>
                <div className="card-inner">
                    <div className="card-title-row">
                        <h3 className="operator-name">{data.operator_name}</h3>
                    </div>
                    <div className="mttr-value-display">
                        <span className="mttr-value">
                            {data.average_mttr_hours > 0 ? data.average_mttr_hours : "---"}
                        </span>
                        <span className="mttr-unit">TIMMAR</span>
                    </div>
                    <div className="card-footer">
                        <span className="analysis-count">
                            {data.outage_count} {lang === "sv" ? "avbrott analyserade" : "outages analyzed"}
                        </span>
                    </div>
                </div>
            </div>
        ));
    } else if (loading) {
        gridContent = <div className="loading-placeholder">Laddar data...</div>;
    } else {
        gridContent = <div className="no-data">Ingen data tillgänglig för valda filter</div>;
    }

    return (
        <div className="prestanda-container animate-fade-in">
            {/* Header section with refined dropdowns matching the mockup */}
            <header className="performance-header">
                <div className="title-group">
                    <h1 className="text-gradient">MTTR Prestanda</h1>
                    <p className="subtitle">
                        {lang === "sv"
                            ? "Genomsnittlig reparationstid per operatör"
                            : "Mean Time To Recovery per operator"}
                    </p>
                </div>

                <div className="filters-row">
                    <div className="premium-filter">
                        <label htmlFor="period-select">TIDSPERIOD</label>
                        <div className="select-wrapper">
                            <select id="period-select" value={period} onChange={(e) => setPeriod(e.target.value)}>
                                <option value="365">{lang === "sv" ? "Ett år" : "One Year"}</option>
                                <option value="90">{lang === "sv" ? "Tre månader" : "Three Months"}</option>
                                <option value="30">{lang === "sv" ? "En månad" : "One Month"}</option>
                                <option value="7">{lang === "sv" ? "En vecka" : "One Week"}</option>
                            </select>
                            <ChevronDown size={14} className="select-icon" />
                        </div>
                    </div>

                    <div className="premium-filter">
                        <label htmlFor="town-select">REGION</label>
                        <div className="select-wrapper">
                            <select id="town-select" value={town} onChange={(e) => setTown(e.target.value)}>
                                <option value="">{lang === "sv" ? "Hela Sverige" : "Entire Sweden"}</option>
                                {locations.map((loc) => (
                                    <option key={loc} value={loc}>{loc}</option>
                                ))}
                            </select>
                            <ChevronDown size={14} className="select-icon" />
                        </div>
                    </div>

                    <div className="premium-filter">
                        <label htmlFor="service-select">TJÄNST</label>
                        <div className="select-wrapper">
                            <select id="service-select" value={service} onChange={(e) => setService(e.target.value)}>
                                <option value="">{lang === "sv" ? "Alla" : "All"}</option>
                                <option value="4G">4G</option>
                                <option value="5G">5G</option>
                            </select>
                            <ChevronDown size={14} className="select-icon" />
                        </div>
                    </div>
                </div>
            </header>

            {/* Info Section matching the mockup's long blue-accented bar */}
            <div className="premium-card info-banner">
                <div className="accent-bar"></div>
                <div className="info-content">
                    <p>
                        {lang === "sv"
                            ? "MTTR (Mean Time To Recovery) mäter den genomsnittliga tiden det tar att laga ett fel. Lägre siffra betyder snabbare reparationer och bättre tillförlitlighet."
                            : "MTTR (Mean Time To Recovery) measures the average time it takes to fix a fault. A lower number means faster repairs and better reliability."
                        }
                    </p>
                </div>
            </div>

            {/* KPI summary bar */}
            {mttrData.length > 0 && (
                <div className="kpi-row">
                    <div className="kpi-card">
                        <Clock size={18} className="kpi-icon" />
                        <div>
                            <div className="kpi-label">{lang === "sv" ? "Snitt MTTR" : "Avg MTTR"}</div>
                            <div className="kpi-value">{avgAll}h</div>
                        </div>
                    </div>
                    <div className="kpi-card">
                        <TrendingDown size={18} className="kpi-icon best" />
                        <div>
                            <div className="kpi-label">{lang === "sv" ? "Snabbast" : "Fastest"}</div>
                            <div className="kpi-value best">{bestOperator?.operator_name} — {bestOperator?.average_mttr_hours}h</div>
                        </div>
                    </div>
                    <div className="kpi-card">
                        <AlertTriangle size={18} className="kpi-icon" />
                        <div>
                            <div className="kpi-label">{lang === "sv" ? "Totalt analyserade" : "Total analyzed"}</div>
                            <div className="kpi-value">{totalOutages}</div>
                        </div>
                    </div>
                    <div className="kpi-card">
                        <CheckCircle size={18} className="kpi-icon" />
                        <div>
                            <div className="kpi-label">{lang === "sv" ? "Operatörer" : "Operators"}</div>
                            <div className="kpi-value">{mttrData.length}</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Bar chart comparison */}
            {mttrData.length > 0 && (
                <div className="premium-card chart-card">
                    <h2 className="section-title">
                        {lang === "sv" ? "MTTR jämförelse" : "MTTR Comparison"}
                    </h2>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={mttrData} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
                            <XAxis dataKey="operator_name" tick={{ fill: "#A0A5B8", fontSize: 13 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#A0A5B8", fontSize: 12 }} axisLine={false} tickLine={false}
                                label={{ value: lang === "sv" ? "Timmar" : "Hours", angle: -90, position: "insideLeft", fill: "#555870", fontSize: 11 }} />
                            <Tooltip
                                contentStyle={{ background: "#1A1D2D", border: "1px solid #2A2E40", borderRadius: 8, color: "#fff" }}
                                formatter={(val) => [`${val}h`, "MTTR"]}
                            />
                            <Bar dataKey="average_mttr_hours" radius={[6, 6, 0, 0]}>
                                {mttrData.map((d) => (
                                    <Cell key={d.operator_name} fill={getOperatorColor(d.operator_name)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Operator Cards Grid */}
            <div className="operator-grid">
                {gridContent}
            </div>

            <style jsx>{`
                .prestanda-container {
                    padding: 40px;
                    max-width: 1300px;
                    margin: 0 auto;
                }

                .performance-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    margin-bottom: 32px;
                }

                .text-gradient {
                    font-size: 2.2rem;
                    font-weight: 800;
                    margin-bottom: 8px;
                    background: linear-gradient(135deg, #fff 0%, #A31FD0 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }

                .subtitle {
                    color: var(--text-muted);
                    font-size: 1rem;
                }

                .filters-row {
                    display: flex;
                    gap: 16px;
                }

                .premium-filter {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .premium-filter label {
                    font-size: 0.65rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    letter-spacing: 0.05em;
                }

                .select-wrapper {
                    position: relative;
                    min-width: 160px;
                }

                .select-wrapper select {
                    width: 100%;
                    appearance: none;
                    background: #1A1D2D;
                    border: 1px solid #2A2E40;
                    border-radius: 8px;
                    padding: 10px 16px;
                    color: #fff;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: border-color 0.2s;
                }

                .select-wrapper select:hover {
                    border-color: #3F445E;
                }

                .select-icon {
                    position: absolute;
                    right: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    pointer-events: none;
                    color: #555870;
                }

                .info-banner {
                    margin-bottom: 40px;
                    padding: 0;
                    display: flex;
                    background: #1A1D2D;
                    border: 1px solid #2A2E40;
                    border-radius: 8px;
                    overflow: hidden;
                    height: 80px;
                }

                .accent-bar {
                    width: 4px;
                    background: #A31FD0;
                    flex-shrink: 0;
                }

                .info-content {
                    padding: 24px;
                    display: flex;
                    align-items: center;
                    font-size: 0.95rem;
                    color: #A0A5B8;
                }

                .operator-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 24px;
                }

                .mttr-card {
                    padding: 0;
                    background: #141724;
                    border: 1px solid #232738;
                    border-radius: 12px;
                    overflow: hidden;
                    transition: transform 0.2s, border-color 0.2s;
                }

                .mttr-card:hover {
                    transform: translateY(-4px);
                    border-color: var(--op-color);
                }

                .card-top-accent {
                    height: 4px;
                    width: 100%;
                    background: var(--op-color);
                    opacity: 0.8;
                }

                .card-inner {
                    padding: 32px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                }

                .card-title-row {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 32px;
                }

                .operator-name {
                    font-size: 1.1rem;
                    font-weight: 700;
                    color: #fff;
                    letter-spacing: 0.1em;
                }

                .simulated-badge {
                    background: #232738;
                    color: #555870;
                    font-size: 0.65rem;
                    font-weight: 700;
                    padding: 2px 8px;
                    border-radius: 4px;
                    text-transform: uppercase;
                }

                .mttr-value-display {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 4px;
                    margin-bottom: 40px;
                }

                .mttr-value {
                    font-size: 5rem;
                    font-weight: 700;
                    color: #fff;
                    line-height: 1;
                }

                .mttr-unit {
                    font-size: 0.8rem;
                    font-weight: 700;
                    color: #555870;
                    letter-spacing: 0.2em;
                }

                .card-footer {
                    margin-top: auto;
                    color: #555870;
                    font-size: 0.8rem;
                }

                .loading-placeholder, .no-data {
                    grid-column: span 3;
                    text-align: center;
                    padding: 60px;
                    color: var(--text-muted);
                    background: #1A1D2D;
                    border-radius: 12px;
                    border: 1px dashed #2A2E40;
                }

                .kpi-row {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 16px;
                    margin-bottom: 24px;
                }
                .kpi-card {
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    background: #1A1D2D;
                    border: 1px solid #2A2E40;
                    border-radius: 10px;
                    padding: 18px 20px;
                }
                .kpi-icon { color: #555870; flex-shrink: 0; }
                .kpi-icon.best { color: #22C55E; }
                .kpi-label { font-size: 0.7rem; color: #555870; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 4px; }
                .kpi-value { font-size: 1.1rem; font-weight: 700; color: #fff; }
                .kpi-value.best { color: #22C55E; font-size: 0.95rem; }

                .chart-card {
                    margin-bottom: 32px;
                    padding: 28px 32px;
                    background: #141724;
                    border: 1px solid #232738;
                    border-radius: 12px;
                }
                .section-title {
                    font-size: 0.8rem;
                    font-weight: 700;
                    color: #555870;
                    letter-spacing: 0.1em;
                    text-transform: uppercase;
                    margin-bottom: 20px;
                }

                @media (max-width: 1024px) {
                    .operator-grid { grid-template-columns: 1fr; }
                    .performance-header { flex-direction: column; align-items: flex-start; gap: 24px; }
                    .kpi-row { grid-template-columns: repeat(2, 1fr); }
                }
            `}</style>
        </div>
    );
}

