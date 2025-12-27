"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { api } from "../../lib/api";

export default function RegionsPage() {
    const { lang, t } = useLanguage();
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRegions = async () => {
            try {
                const data = await api.regions.list();
                setRegions(data);
            } catch (err) {
                console.error("Failed to fetch regions:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchRegions();
    }, []);

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;

    return (
        <div className="regions-container animate-fade-in">
            <header className="page-header">
                <h1 className="text-gradient">
                    {lang === "sv" ? "Regional Status" : "Regional Health"}
                </h1>
                <p className="subtitle">
                    {lang === "sv" ? "Nätverksstabilitet per län" : "Network stability by Swedish county"}
                </p>
            </header>

            <div className="regions-grid">
                {regions.map((region) => (
                    <div key={region.id} className="premium-card region-card">
                        <div className="region-info">
                            <h3 className="region-name">{t(region.name)}</h3>
                            <div className="region-status">
                                <span className={`status-dot ${region.outage_count > 0 ? "warning" : "stable"}`}></span>
                                <span className="status-label">
                                    {region.outage_count > 0
                                        ? `${region.outage_count} ${lang === "sv" ? "aktiva incidenter" : "active incidents"}`
                                        : (lang === "sv" ? "Inga störningar" : "No disruptions")}
                                </span>
                            </div>
                        </div>
                        <div className="region-meta">
                            <span className="uptime">100% Up</span>
                        </div>
                    </div>
                ))}
            </div>

            <style jsx>{`
                .regions-container {
                    padding: 32px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .page-header { margin-bottom: 40px; }
                .page-header h1 { font-size: 1.8rem; margin-bottom: 4px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }

                .regions-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 16px;
                }
                .region-card {
                    padding: 24px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .region-name { font-size: 1rem; margin-bottom: 8px; font-weight: 700; }
                .region-status { display: flex; align-items: center; gap: 8px; }
                .status-dot { width: 6px; height: 6px; border-radius: 50%; }
                .status-dot.stable { background: var(--status-success); }
                .status-dot.warning { background: var(--status-warning); }
                
                .status-label { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
                .uptime { font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; }

                .loading-container { height: 60vh; display: flex; align-items: center; justify-content: center; }
                .spinner {
                    width: 32px; height: 32px;
                    border: 3px solid var(--border-color);
                    border-top-color: var(--accent-primary);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin { to { transform: rotate(360deg); } }

                @media (max-width: 768px) {
                    .regions-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
