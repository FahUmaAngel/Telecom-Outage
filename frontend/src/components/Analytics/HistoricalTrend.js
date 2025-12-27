"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useLanguage } from '../../context/LanguageContext';

export default function HistoricalTrend({ data }) {
    const { lang } = useLanguage();

    if (!data || !data.trend || data.trend.length === 0) {
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

    // Format dates for display (show only last 7 days labels to avoid clutter)
    const formattedData = data.trend.map((d, idx) => ({
        ...d,
        displayDate: idx % 4 === 0 ? d.date.substring(5) : '' // Show every 4th date (MM-DD)
    }));

    return (
        <div className="trend-chart">
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={formattedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                    <XAxis
                        dataKey="displayDate"
                        stroke="var(--text-secondary)"
                        tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                    />
                    <YAxis
                        stroke="var(--text-secondary)"
                        tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'var(--surface-base)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)'
                        }}
                        labelFormatter={(label, payload) => {
                            if (payload && payload[0]) {
                                return payload[0].payload.date;
                            }
                            return label;
                        }}
                        formatter={(value) => [value, lang === "sv" ? "Avbrott" : "Outages"]}
                    />
                    <Line
                        type="monotone"
                        dataKey="count"
                        stroke="var(--accent-primary)"
                        strokeWidth={2}
                        dot={{ fill: 'var(--accent-primary)', r: 4 }}
                        activeDot={{ r: 6 }}
                    />
                </LineChart>
            </ResponsiveContainer>

            <div className="chart-summary">
                <span className="summary-label">
                    {lang === "sv" ? "Totalt antal avbrott (30 dagar):" : "Total outages (30 days):"}
                </span>
                <span className="summary-value">{data.total_count}</span>
            </div>

            <style jsx>{`
                .trend-chart {
                    padding: 20px;
                }
                .chart-summary {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    margin-top: 20px;
                    padding-top: 15px;
                    border-top: 1px solid var(--glass-border);
                }
                .summary-label {
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
                .summary-value {
                    color: var(--accent-primary);
                    font-size: 1.5rem;
                    font-weight: 700;
                }
            `}</style>
        </div>
    );
}
