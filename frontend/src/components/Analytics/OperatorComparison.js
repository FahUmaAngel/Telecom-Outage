"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useLanguage } from '../../context/LanguageContext';

export default function OperatorComparison({ mttrData, reliabilityData }) {
    const { lang } = useLanguage();

    if (!mttrData || !reliabilityData || mttrData.length === 0) {
        return (
            <div className="empty-chart glass">
                <p>{lang === "sv" ? "Ingen data tillgänglig" : "No data available"}</p>
                <style jsx>{`
                    .empty-chart {
                        height: 300px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: var(--text-muted);
                    }
                `}</style>
            </div>
        );
    }

    // Combine MTTR and Reliability data
    const comparisonData = mttrData.map(mttr => {
        const reliability = reliabilityData.find(r => r.operator_name === mttr.operator_name);

        // Calculate reliability percentage (simple formula: 100 - (downtime_hours / 720 * 100))
        // 720 hours = 30 days
        const reliabilityPercent = reliability
            ? Math.max(0, 100 - (reliability.total_downtime_hours / 720 * 100)).toFixed(1)
            : 0;

        return {
            name: mttr.operator_name.charAt(0).toUpperCase() + mttr.operator_name.slice(1),
            mttr: parseFloat(mttr.average_mttr_hours.toFixed(1)),
            outages: reliability ? reliability.outage_count : 0,
            reliability: parseFloat(reliabilityPercent)
        };
    });

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip glass">
                    <p className="label">{label}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }}>
                            {entry.name}: {entry.value}
                            {entry.dataKey === 'reliability' ? '%' : entry.dataKey === 'mttr' ? 'h' : ''}
                        </p>
                    ))}
                    <style jsx>{`
                        .custom-tooltip {
                            padding: 12px;
                            border-radius: 8px;
                            border: 1px solid var(--glass-border);
                        }
                        .label {
                            font-weight: 700;
                            margin-bottom: 8px;
                            color: var(--text-primary);
                        }
                        p {
                            margin: 4px 0;
                            font-size: 0.9rem;
                        }
                    `}</style>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="operator-comparison">
            <div className="charts-grid">
                {/* MTTR Comparison */}
                <div className="chart-section">
                    <h3>{lang === "sv" ? "Genomsnittlig reparationstid (MTTR)" : "Mean Time to Repair (MTTR)"}</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={comparisonData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                            <XAxis
                                dataKey="name"
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            />
                            <YAxis
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                label={{
                                    value: lang === "sv" ? 'Timmar' : 'Hours',
                                    angle: -90,
                                    position: 'insideLeft',
                                    style: { fill: 'var(--text-secondary)' }
                                }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar
                                dataKey="mttr"
                                fill="#f59e0b"
                                name={lang === "sv" ? "MTTR (timmar)" : "MTTR (hours)"}
                                radius={[8, 8, 0, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                    <p className="chart-note">
                        {lang === "sv" ? "Lägre är bättre" : "Lower is better"}
                    </p>
                </div>

                {/* Outage Count Comparison */}
                <div className="chart-section">
                    <h3>{lang === "sv" ? "Antal avbrott (30 dagar)" : "Outage Count (30 days)"}</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={comparisonData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                            <XAxis
                                dataKey="name"
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            />
                            <YAxis
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                label={{
                                    value: lang === "sv" ? 'Antal' : 'Count',
                                    angle: -90,
                                    position: 'insideLeft',
                                    style: { fill: 'var(--text-secondary)' }
                                }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar
                                dataKey="outages"
                                fill="#ef4444"
                                name={lang === "sv" ? "Avbrott" : "Outages"}
                                radius={[8, 8, 0, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                    <p className="chart-note">
                        {lang === "sv" ? "Lägre är bättre" : "Lower is better"}
                    </p>
                </div>

                {/* Reliability Comparison */}
                <div className="chart-section">
                    <h3>{lang === "sv" ? "Nätverkstillförlitlighet" : "Network Reliability"}</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={comparisonData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                            <XAxis
                                dataKey="name"
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            />
                            <YAxis
                                stroke="var(--text-secondary)"
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                domain={[0, 100]}
                                label={{
                                    value: '%',
                                    angle: -90,
                                    position: 'insideLeft',
                                    style: { fill: 'var(--text-secondary)' }
                                }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar
                                dataKey="reliability"
                                fill="#10b981"
                                name={lang === "sv" ? "Tillförlitlighet" : "Reliability"}
                                radius={[8, 8, 0, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                    <p className="chart-note">
                        {lang === "sv" ? "Högre är bättre" : "Higher is better"}
                    </p>
                </div>
            </div>

            <style jsx>{`
                .operator-comparison {
                    padding: 20px;
                }
                .charts-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 30px;
                }
                .chart-section h3 {
                    margin-bottom: 16px;
                    color: var(--text-primary);
                    font-size: 1.1rem;
                }
                .chart-note {
                    margin-top: 8px;
                    text-align: center;
                    font-size: 0.85rem;
                    color: var(--text-muted);
                    font-style: italic;
                }

                @media (max-width: 768px) {
                    .charts-grid {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>
        </div>
    );
}
