"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "../../context/LanguageContext";
import { api } from "../../lib/api";
import ReportForm from "../../components/Report/ReportForm";

export default function ReportPage() {
    const { lang } = useLanguage();
    const [operators, setOperators] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchOperators = async () => {
            try {
                const data = await api.operators.list();
                setOperators(data);
            } catch (error) {
                console.error("Failed to fetch operators:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchOperators();
    }, []);

    if (loading) {
        return (
            <div className="loading-state">
                <div className="spinner"></div>
                <style jsx>{`
                    .loading-state {
                        height: 60vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .spinner {
                        width: 40px;
                        height: 40px;
                        border: 3px solid var(--surface-light);
                        border-top-color: var(--accent-primary);
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    }
                    @keyframes spin { to { transform: rotate(360deg); } }
                `}</style>
            </div>
        );
    }

    return (
        <div className="report-page animate-fade-in">
            <header className="page-header">
                <h1 className="text-gradient">
                    {lang === "sv" ? "Rapportera avbrott" : "Report Outage"}
                </h1>
                <p className="subtitle">
                    {lang === "sv"
                        ? "Bidra med information om nätverksproblem i ditt område"
                        : "Submit information regarding network issues in your area"}
                </p>
            </header>

            <div className="premium-card form-container">
                <ReportForm operators={operators} />
            </div>

            <div className="info-grid">
                <div className="info-card">
                    <h3 className="card-title">{lang === "sv" ? "Varför rapportera?" : "Crowdsourced Data"}</h3>
                    <p className="card-text">
                        {lang === "sv"
                            ? "Dina rapporter hjälper oss att identifiera problemområden och ge realtidsinformation till alla användare."
                            : "Your reports help identify local disruptions and provide shared visibility for the community."}
                    </p>
                </div>
                <div className="info-card">
                    <h3 className="card-title">{lang === "sv" ? "Integritet" : "Data Privacy"}</h3>
                    <p className="card-text">
                        {lang === "sv"
                            ? "Vi loggar endast din ungefärliga geografiska position för kartvisualisering. Ingen personlig data lagras."
                            : "We only log approximate coordinates for map visualization. No personal identifiable information is retained."}
                    </p>
                </div>
            </div>

            <style jsx>{`
                .report-page {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 32px;
                }
                .page-header {
                    margin-bottom: 40px;
                    padding-bottom: 24px;
                    border-bottom: 1px solid var(--border-color);
                }
                .page-header h1 { font-size: 1.8rem; margin-bottom: 6px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }
                
                .form-container {
                    padding: 40px;
                    margin-bottom: 40px;
                }
                
                .info-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }
                .info-card {
                    padding: 24px;
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-md);
                }
                .card-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 12px; color: var(--text-primary); text-transform: uppercase; }
                .card-text { color: var(--text-muted); line-height: 1.6; font-size: 0.9rem; }

                @media (max-width: 768px) {
                    .report-page { padding: 20px; }
                    .form-container { padding: 24px; }
                    .info-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
