"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import PropTypes from 'prop-types';
import { useLanguage } from '../../context/LanguageContext';


function getUnitSuffix(dataKey) {
    if (dataKey === 'reliability') return '%';
    if (dataKey === 'mttr') return 'h';
    return '';
}

function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || payload.length === 0) {
        return null;
    }
    return (
        <div className="custom-tooltip glass">
            <p className="label">{label}</p>
            {payload.map((entry) => (
                <p key={entry.dataKey} style={{ color: entry.color }}>
                    {entry.name}: {entry.value}{getUnitSuffix(entry.dataKey)}
                </p>
            ))}
        </div>
    );
}

CustomTooltip.propTypes = {
    active: PropTypes.bool,
    label: PropTypes.string,
    payload: PropTypes.arrayOf(PropTypes.shape({
        color: PropTypes.string,
        name: PropTypes.string,
        value: PropTypes.number,
        dataKey: PropTypes.string,
    })),
};

CustomTooltip.defaultProps = { active: false, label: '', payload: [] };

function buildComparisonData(mttrData, reliabilityData) {
    return mttrData.map(mttr => {
        const reliability = reliabilityData.find(r => r.operator_name === mttr.operator_name);
        const reliabilityPercent = reliability
            ? Math.max(0, 100 - (reliability.total_downtime_hours / 720 * 100)).toFixed(1)
            : 0;
        return {
            name: mttr.operator_name.charAt(0).toUpperCase() + mttr.operator_name.slice(1),
            mttr: Number.parseFloat(mttr.average_mttr_hours.toFixed(1)),
            outages: reliability ? reliability.outage_count : 0,
            reliability: Number.parseFloat(reliabilityPercent),
        };
    });
}

function MttrChart({ comparisonData, lang }) {
    const emptyLabel = lang === "sv" ? "Inga lösta avbrott hittades ännu" : "No resolved outages found yet";
    const titleLabel = lang === "sv" ? "Genomsnittlig reparationstid (MTTR)" : "Mean Time to Repair (MTTR)";
    const hoursLabel = lang === "sv" ? 'Timmar' : 'Hours';
    const barName = lang === "sv" ? "MTTR (timmar)" : "MTTR (hours)";
    const noteLabel = lang === "sv" ? "Lägre är bättre" : "Lower is better";

    return (
        <div className="chart-section">
            <h3>{titleLabel}</h3>
            {comparisonData.every(d => d.mttr === 0) ? (
                <div className="empty-chart glass" style={{ height: '250px' }}>
                    <p>{emptyLabel}</p>
                </div>
            ) : (
                <>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={comparisonData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                            <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                            <YAxis stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                label={{ value: hoursLabel, angle: -90, position: 'insideLeft', style: { fill: 'var(--text-secondary)' } }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="mttr" fill="#f59e0b" name={barName} radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                    <p className="chart-note">{noteLabel}</p>
                </>
            )}
        </div>
    );
}

MttrChart.propTypes = {
    comparisonData: PropTypes.array.isRequired,
    lang: PropTypes.string.isRequired,
};

function OutageCountChart({ comparisonData, lang }) {
    const titleLabel = lang === "sv" ? "Antal avbrott (30 dagar)" : "Outage Count (30 days)";
    const countLabel = lang === "sv" ? 'Antal' : 'Count';
    const barName = lang === "sv" ? "Avbrott" : "Outages";
    const noteLabel = lang === "sv" ? "Lägre är bättre" : "Lower is better";

    return (
        <div className="chart-section">
            <h3>{titleLabel}</h3>
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                    <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                    <YAxis stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        label={{ value: countLabel, angle: -90, position: 'insideLeft', style: { fill: 'var(--text-secondary)' } }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="outages" fill="#ef4444" name={barName} radius={[8, 8, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
            <p className="chart-note">{noteLabel}</p>
        </div>
    );
}

OutageCountChart.propTypes = {
    comparisonData: PropTypes.array.isRequired,
    lang: PropTypes.string.isRequired,
};

function ReliabilityChart({ comparisonData, lang }) {
    const titleLabel = lang === "sv" ? "Nätverkstillförlitlighet" : "Network Reliability";
    const barName = lang === "sv" ? "Tillförlitlighet" : "Reliability";
    const noteLabel = lang === "sv" ? "Högre är bättre" : "Higher is better";

    return (
        <div className="chart-section">
            <h3>{titleLabel}</h3>
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" />
                    <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                    <YAxis stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        domain={[0, 100]}
                        label={{ value: '%', angle: -90, position: 'insideLeft', style: { fill: 'var(--text-secondary)' } }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="reliability" fill="#10b981" name={barName} radius={[8, 8, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
            <p className="chart-note">{noteLabel}</p>
        </div>
    );
}

ReliabilityChart.propTypes = {
    comparisonData: PropTypes.array.isRequired,
    lang: PropTypes.string.isRequired,
};


export default function OperatorComparison({ mttrData, reliabilityData }) {
    const { lang } = useLanguage();

    if (!mttrData || !reliabilityData || mttrData.length === 0) {
        return (
            <div className="empty-chart glass">
                <p>{lang === "sv" ? "Ingen data tillgänglig" : "No data available"}</p>
                <style jsx global>{`
                    .empty-chart { height: 300px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
                `}</style>
            </div>
        );
    }

    const comparisonData = buildComparisonData(mttrData, reliabilityData);



    return (
        <div className="operator-comparison">
            <div className="charts-grid">
                <MttrChart comparisonData={comparisonData} lang={lang} />
                <OutageCountChart comparisonData={comparisonData} lang={lang} />
                <ReliabilityChart comparisonData={comparisonData} lang={lang} />
            </div>

            <style jsx global>{`
                .operator-comparison { padding: 20px; }
                .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; }
                .chart-section h3 { margin-bottom: 16px; color: var(--text-primary); font-size: 1.1rem; }
                .chart-note { margin-top: 8px; text-align: center; font-size: 0.85rem; color: var(--text-muted); font-style: italic; }
                .custom-tooltip { padding: 12px; border-radius: 8px; border: 1px solid var(--glass-border); }
                .custom-tooltip .label { font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }
                .custom-tooltip p { margin: 4px 0; font-size: 0.9rem; }
                @media (max-width: 768px) { .charts-grid { grid-template-columns: 1fr; } }
            `}</style>
        </div>
    );
}

OperatorComparison.propTypes = {
    mttrData: PropTypes.arrayOf(PropTypes.shape({
        operator_name: PropTypes.string,
        average_mttr_hours: PropTypes.number,
        outage_count: PropTypes.number,
    })),
    reliabilityData: PropTypes.arrayOf(PropTypes.shape({
        operator_name: PropTypes.string,
        total_downtime_hours: PropTypes.number,
        outage_count: PropTypes.number,
    })),
};

OperatorComparison.defaultProps = { mttrData: [], reliabilityData: [] };
