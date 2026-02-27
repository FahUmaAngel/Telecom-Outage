"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { api } from "../../lib/api";

export default function MTTRPage() {
    const { lang } = useLanguage();
    const [timeRange, setTimeRange] = useState(365); // Default 1 year
    const [city, setCity] = useState("");
    const [cities, setCities] = useState([]);
    const [mttrData, setMttrData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCities = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/v1/analytics/cities");
                const data = await response.json();
                setCities(data);
            } catch (err) {
                console.error("Failed to fetch cities:", err);
            }
        };
        fetchCities();
    }, []);

    useEffect(() => {
        const fetchMTTR = async () => {
            setLoading(true);
            try {
                const url = `http://localhost:8000/api/v1/analytics/mttr-dynamic?days=${timeRange}${city ? `&city=${encodeURIComponent(city)}` : ""}`;
                const response = await fetch(url);
                const data = await response.json();
                setMttrData(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error("Failed to fetch MTTR data:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchMTTR();
    }, [timeRange, city]);

    return (
        <div className="mttr-container animate-fade-in">
            <header className="page-header">
                <div className="header-content">
                    <h1 className="text-gradient">
                        {lang === "sv" ? "MTTR Prestanda" : "MTTR Performance"}
                    </h1>
                    <p className="subtitle">
                        {lang === "sv" ? "Genomsnittlig reparationstid per operatör" : "Average recovery time per operator"}
                    </p>
                </div>

                <div className="selectors-container">
                    <div className="select-wrapper">
                        <label>{lang === "sv" ? "Tidsperiod" : "Time Period"}</label>
                        <select value={timeRange} onChange={(e) => setTimeRange(Number(e.target.value))}>
                            <option value={365}>{lang === "sv" ? "Ett år" : "One Year"}</option>
                            <option value={180}>{lang === "sv" ? "6 månader" : "6 Months"}</option>
                            <option value={90}>{lang === "sv" ? "3 månader" : "3 Months"}</option>
                            <option value={30}>{lang === "sv" ? "En månad" : "One Month"}</option>
                        </select>
                    </div>

                    <div className="select-wrapper">
                        <label>{lang === "sv" ? "Stad (Data för Tre)" : "City (Data for Tre)"}</label>
                        <select value={city} onChange={(e) => setCity(e.target.value)}>
                            <option value="">{lang === "sv" ? "Hela Sverige" : "All Sweden"}</option>
                            {cities.map(c => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </header>

            <div className="explanation-banner premium-card">
                <p>
                    {lang === "sv"
                        ? "MTTR (Mean Time To Recovery) mäter den genomsnittliga tiden det tar att laga ett fel. Lägre siffra betyder snabbare reparationer och bättre tillförlitlighet."
                        : "MTTR (Mean Time To Recovery) measures the average time to fix a fault. A lower number means faster repairs and better reliability."
                    }
                </p>
            </div>

            <div className="kpi-grid">
                {mttrData.map((item) => (
                    <div key={item.operator_name} className={`premium-card kpi-card ${item.operator_name.toLowerCase()}`}>
                        <div className="op-header">
                            <span className="op-name">{item.operator_name.toUpperCase()}</span>
                            {!item.is_real && <span className="placeholder-tag">{lang === "sv" ? "Simulerat" : "Placeholder"}</span>}
                        </div>
                        <div className="mttr-value">
                            <span className="number">{item.average_mttr_hours}</span>
                            <span className="unit">{lang === "sv" ? "timmar" : "hours"}</span>
                        </div>
                        <div className="outage-count">
                            {item.outage_count} {lang === "sv" ? "avbrott analyserade" : "outages analyzed"}
                        </div>
                    </div>
                ))}
            </div>

            <style jsx>{`
                .mttr-container {
                    padding: 32px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    margin-bottom: 32px;
                    gap: 24px;
                    flex-wrap: wrap;
                }
                .explanation-banner {
                    margin-bottom: 32px;
                    padding: 20px 24px;
                    background: var(--surface-hover);
                    border-left: 4px solid var(--accent-primary);
                    font-size: 0.95rem;
                    color: var(--text-secondary);
                    line-height: 1.5;
                }
                .selectors-container {
                    display: flex;
                    gap: 20px;
                }
                .select-wrapper {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                .select-wrapper label {
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    color: var(--text-muted);
                    font-weight: 700;
                    letter-spacing: 0.05em;
                }
                .select-wrapper select {
                    padding: 10px 16px;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    background: var(--surface-color);
                    color: var(--text-primary);
                    font-size: 0.9rem;
                    cursor: pointer;
                    min-width: 180px;
                }
                
                .kpi-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 24px;
                }
                .kpi-card {
                    padding: 32px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }
                .kpi-card::before {
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 4px;
                }
                .kpi-card.telia::before { background: #9933cc; }
                .kpi-card.tre::before { background: #f36f21; }
                .kpi-card.lycamobile::before { background: #004b91; }

                .op-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 20px;
                }
                .op-name {
                    font-size: 1.1rem;
                    font-weight: 800;
                    letter-spacing: 0.1em;
                    color: var(--text-secondary);
                }
                .placeholder-tag {
                    font-size: 0.6rem;
                    background: var(--surface-hover);
                    padding: 2px 6px;
                    border-radius: 4px;
                    border: 1px solid var(--border-color);
                    color: var(--text-muted);
                }

                .mttr-value {
                    margin: 20px 0;
                }
                .mttr-value .number {
                    font-size: 4.5rem;
                    font-weight: 900;
                    line-height: 1;
                    display: block;
                    background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .mttr-value .unit {
                    font-size: 1rem;
                    color: var(--text-muted);
                    text-transform: uppercase;
                    font-weight: 700;
                    letter-spacing: 0.1em;
                }

                .outage-count {
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                    margin-top: 12px;
                }

                @media (max-width: 768px) {
                    .page-header { flex-direction: column; align-items: flex-start; }
                    .selectors-container { width: 100%; flex-direction: column; }
                    .select-wrapper select { width: 100%; }
                }
            `}</style>
        </div>
    );
}
