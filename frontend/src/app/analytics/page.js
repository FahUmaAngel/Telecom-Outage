"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { api } from "../../lib/api";
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Cell
} from 'recharts';

export default function AnalyticsPage() {
    const { lang } = useLanguage();
    const [trend, setTrend] = useState([]);
    const [reliability, setReliability] = useState([]);
    const [mttr, setMttr] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const [trendData, reliabilityData, mttrData] = await Promise.all([
                    api.outages.history(),
                    api.outages.reliability(),
                    api.outages.mttr()
                ]);
                setTrend(trendData.trend || []);
                setReliability(reliabilityData);
                setMttr(mttrData);
            } catch (err) {
                console.error("Failed to fetch analytics:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
    }, []);

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;

    // Map operator reliability to include relative scores for visualization
    const reliabilityChartData = reliability.map(r => ({
        name: r.operator_name.toUpperCase(),
        count: r.outage_count,
        downtime: r.total_downtime_hours,
        // Calculate a mock score for bar width if downtime is high
        score: Math.max(10, 100 - (r.total_downtime_hours / 10))
    }));

    // Map history trend for the line chart
    const trendChartData = trend.map(t => ({
        day: new Date(t.date).toLocaleDateString([], { weekday: 'short' }),
        count: t.count
    }));

    const avgMttr = mttr.length > 0
        ? (mttr.reduce((acc, curr) => acc + curr.average_mttr_hours, 0) / mttr.length).toFixed(1)
        : "0";

    return (
        <div className="analytics-container animate-fade-in">
            <header className="page-header">
                <h1 className="text-gradient">
                    {lang === "sv" ? "Nätverksanalys" : "Network Analytics"}
                </h1>
                <p className="subtitle">
                    {lang === "sv" ? "Prestandamått och historiska trender" : "Performance tracking and historical trends"}
                </p>
            </header>

            <div className="analytics-grid">
                <div className="premium-card chart-card wide">
                    <h3 className="chart-title">{lang === "sv" ? "Incident-trend (Senaste 30 dagarna)" : "Incident Trend (Last 30 Days)"}</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={trendChartData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                                    itemStyle={{ color: 'var(--accent-primary)', fontWeight: 700 }}
                                />
                                <Line type="monotone" dataKey="count" stroke="var(--accent-primary)" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="premium-card chart-card">
                    <h3 className="chart-title">{lang === "sv" ? "Operatörspålitlighet (Stabilast)" : "Operator Reliability (Stability Score)"}</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={reliabilityChartData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-color)" />
                                <XAxis type="number" domain={[0, 100]} hide />
                                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-primary)', fontWeight: 700, fontSize: 10 }} />
                                <Tooltip cursor={{ fill: 'var(--surface-hover)' }} />
                                <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
                                    {reliabilityChartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index === 0 ? 'var(--accent-primary)' : 'var(--text-muted)'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="premium-card stats-card">
                    <h3 className="chart-title">{lang === "sv" ? "Snabba Insikter" : "Quick Insights"}</h3>
                    <div className="insights-list">
                        <div className="insight-item">
                            <span className="insight-label">Mean Time To Repair (MTTR)</span>
                            <span className="insight-value">{avgMttr === "0" ? "-" : `${avgMttr}h`}</span>
                        </div>
                        <div className="insight-item">
                            <span className="insight-label">{lang === "sv" ? "Totala Incidenter" : "Total Incidents"}</span>
                            <span className="insight-value">{trend.reduce((acc, curr) => acc + curr.count, 0)}</span>
                        </div>
                        <div className="insight-item">
                            <span className="insight-label">{lang === "sv" ? "Mest påverkade operatörer" : "Most Impacted Operators"}</span>
                            <span className="insight-value">{reliability.length}</span>
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
                .analytics-container {
                    padding: 32px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .page-header { margin-bottom: 40px; }
                .page-header h1 { font-size: 1.8rem; margin-bottom: 4px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }

                .analytics-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 24px;
                }
                .chart-card.wide { grid-column: span 2; }
                .chart-card, .stats-card { padding: 32px; }
                .chart-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 32px; color: var(--text-muted); text-transform: uppercase; }
                
                .chart-container { width: 100%; }

                .insights-list { display: flex; flex-direction: column; gap: 20px; }
                .insight-item { display: flex; justify-content: space-between; align-items: baseline; }
                .insight-label { font-size: 0.85rem; color: var(--text-muted); }
                .insight-value { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); }

                .loading-container { height: 60vh; display: flex; align-items: center; justify-content: center; }
                .spinner {
                    width: 32px; height: 32px;
                    border: 3px solid var(--border-color);
                    border-top-color: var(--accent-primary);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin { to { transform: rotate(360deg); } }

                @media (max-width: 1100px) {
                    .analytics-grid { grid-template-columns: 1fr; }
                    .chart-card.wide { grid-column: span 1; }
                }
            `}</style>
        </div>
    );
}
