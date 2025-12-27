"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "../../../lib/api";
import { useLanguage } from "../../../context/LanguageContext";
import Link from "next/link";

export default function OutageDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const { lang, t } = useLanguage();
    const [outage, setOutage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOutage = async () => {
            try {
                const data = await api.outages.get(id);
                setOutage(data);
            } catch (err) {
                console.error("Failed to fetch outage details:", err);
                setError(lang === "sv" ? "Kunde inte hämta information om avbrottet." : "Failed to fetch outage details.");
            } finally {
                setLoading(false);
            }
        };

        if (id) fetchOutage();
    }, [id, lang]);

    if (loading) {
        return (
            <div className="detail-page-loading">
                <div className="spinner"></div>
                <style jsx>{`
                    .detail-page-loading {
                        height: 70vh;
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

    if (error || !outage) {
        return (
            <div className="error-state glass">
                <h2>{error || (lang === "sv" ? "Avbrottet hittades inte" : "Outage not found")}</h2>
                <button onClick={() => router.back()} className="back-btn">
                    {lang === "sv" ? "Gå tillbaka" : "Go back"}
                </button>
                <style jsx>{`
                    .error-state {
                        padding: 40px;
                        text-align: center;
                        margin-top: 50px;
                    }
                    .back-btn {
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: var(--accent-primary);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                    }
                `}</style>
            </div>
        );
    }

    return (
        <div className="outage-detail-container animate-fade-in">
            <header className="detail-header">
                <Link href="/" className="back-link">
                    <span className="arrow">←</span> {lang === "sv" ? "Tillbaka" : "Dashboard"}
                </Link>
                <div className={`status-badge-detail status-${outage.status.toLowerCase()}`}>
                    {outage.status}
                </div>
            </header>

            <div className="detail-grid">
                <div className="main-column">
                    <section className="premium-card hero-section">
                        <h1 className="detail-title">{t(outage.title)}</h1>

                        <div className="meta-info-grid">
                            <div className="info-item">
                                <span className="info-label">{lang === "sv" ? "Operatör" : "Operator"}</span>
                                <span className="info-value">{outage.operator_name}</span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">{lang === "sv" ? "Plats" : "Location"}</span>
                                <span className="info-value">{outage.location || "Sweden"}</span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">{lang === "sv" ? "Allvarlighetsgrad" : "Severity"}</span>
                                <span className={`info-value severity-${outage.severity.toLowerCase()}`}>
                                    {outage.severity}
                                </span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">{lang === "sv" ? "Starttid" : "Started"}</span>
                                <span className="info-value">{new Date(outage.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                            </div>
                        </div>

                        <div className="description-section">
                            <h4 className="sub-title">{lang === "sv" ? "Beskrivning" : "Description"}</h4>
                            <p className="description-text">{t(outage.description)}</p>
                        </div>

                        {outage.affected_services?.length > 0 && (
                            <div className="services-section">
                                <h4 className="sub-title">{lang === "sv" ? "Berörda tjänster" : "Affected Services"}</h4>
                                <div className="service-list">
                                    {outage.affected_services.map(service => (
                                        <span key={service} className="service-tag">{service}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </section>

                    <section className="premium-card history-section">
                        <h3 className="section-title">{lang === "sv" ? "Händelseförlopp" : "Timeline"}</h3>
                        <div className="timeline-flow">
                            <div className="timeline-step">
                                <div className="step-dot critical"></div>
                                <div className="step-content">
                                    <div className="step-top">
                                        <span className="step-label">{lang === "sv" ? "Upptäckt" : "Detected"}</span>
                                        <span className="step-time">{new Date(outage.start_time).toLocaleString()}</span>
                                    </div>
                                    <p className="step-desc">
                                        {lang === "sv"
                                            ? `Incident hos ${outage.operator_name} identifierad.`
                                            : `Incident at ${outage.operator_name} identified.`}
                                    </p>
                                </div>
                            </div>

                            {outage.updated_at && new Date(outage.updated_at) > new Date(outage.start_time) && (
                                <div className="timeline-step">
                                    <div className="step-dot indigo"></div>
                                    <div className="step-content">
                                        <div className="step-top">
                                            <span className="step-label">{lang === "sv" ? "Uppdatering" : "Update"}</span>
                                            <span className="step-time">{new Date(outage.updated_at).toLocaleString()}</span>
                                        </div>
                                        <p className="step-desc">
                                            {lang === "sv"
                                                ? "Analys och felsökning pågår."
                                                : "Analysis and troubleshooting in progress."}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {outage.status === "resolved" && (
                                <div className="timeline-step">
                                    <div className="step-dot success"></div>
                                    <div className="step-content">
                                        <div className="step-top">
                                            <span className="step-label">{lang === "sv" ? "Löst" : "Resolved"}</span>
                                            <span className="step-time">{outage.end_time ? new Date(outage.end_time).toLocaleString() : new Date(outage.updated_at).toLocaleString()}</span>
                                        </div>
                                        <p className="step-desc">
                                            {lang === "sv"
                                                ? "Tjänsten är återställd."
                                                : "Service has been restored."}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </section>
                </div>

                <aside className="details-sidebar">
                    <div className="premium-card status-panel">
                        <h3 className="panel-title">{lang === "sv" ? "Status" : "Summary"}</h3>
                        <div className="summary-datum">
                            <span className="datum-label">{lang === "sv" ? "Senaste synk" : "Last Sync"}</span>
                            <span className="datum-value">
                                {outage.updated_at ? new Date(outage.updated_at).toLocaleTimeString() : new Date(outage.start_time).toLocaleTimeString()}
                            </span>
                        </div>
                        {outage.estimated_fix_time && (
                            <div className="summary-datum highlight">
                                <span className="datum-label">{lang === "sv" ? "Beräknad lösning" : "ETA Resolution"}</span>
                                <span className="datum-value indigo-text">{new Date(outage.estimated_fix_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                <span className="datum-sub">{new Date(outage.estimated_fix_time).toLocaleDateString()}</span>
                            </div>
                        )}
                        <button className="btn-refresh" onClick={() => window.location.reload()}>
                            {lang === "sv" ? "Uppdatera" : "Refresh"}
                        </button>
                        {outage.source_url && (
                            <a href={outage.source_url} target="_blank" rel="noopener noreferrer" className="btn-source">
                                {lang === "sv" ? "Visa källa" : "View Source"} ↗
                            </a>
                        )}
                    </div>
                </aside>
            </div>

            <style jsx>{`
                .outage-detail-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 32px;
                }
                .detail-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 32px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid var(--border-color);
                }
                .back-link {
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .back-link:hover {
                    color: var(--accent-primary);
                }
                
                .status-badge-detail {
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-weight: 700;
                    text-transform: uppercase;
                    font-size: 0.7rem;
                    letter-spacing: 0.05em;
                    border: 1px solid var(--border-color);
                }
                .status-active { color: var(--status-critical); border-color: var(--status-critical); }
                .status-resolved { color: var(--status-success); border-color: var(--status-success); }

                .detail-grid {
                    display: grid;
                    grid-template-columns: 1fr 340px;
                    gap: 32px;
                }
                .hero-section { padding: 32px; margin-bottom: 24px; }
                .detail-title { font-size: 1.8rem; margin-bottom: 32px; font-weight: 700; }
                
                .meta-info-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-bottom: 32px;
                    padding: 24px;
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-md);
                }
                .info-item { display: flex; flex-direction: column; gap: 4px; }
                .info-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
                .info-value { font-size: 1rem; font-weight: 600; color: var(--text-primary); }
                
                .severity-critical { color: var(--status-critical); }
                
                .sub-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 12px; text-transform: uppercase; color: var(--text-muted); }
                .description-text { line-height: 1.6; color: var(--text-secondary); font-size: 0.95rem; }
                
                .description-section { margin-top: 32px; }
                .services-section { margin-top: 32px; }
                .service-list { display: flex; gap: 8px; flex-wrap: wrap; }
                .service-tag {
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    background: var(--surface-hover);
                    border: 1px solid var(--border-color);
                    color: var(--text-secondary);
                }

                .history-section { padding: 32px; }
                .section-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 24px; }
                .timeline-flow {
                    display: flex;
                    flex-direction: column;
                }
                .timeline-step {
                    display: flex;
                    gap: 20px;
                    padding-bottom: 32px;
                    position: relative;
                }
                .timeline-step:not(:last-child)::after {
                    content: '';
                    position: absolute;
                    left: 2.5px;
                    top: 14px;
                    bottom: 0;
                    width: 1px;
                    background: var(--border-color);
                }
                .step-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: var(--text-muted);
                    flex-shrink: 0;
                    margin-top: 6px;
                    z-index: 1;
                }
                .step-dot.critical { background: var(--status-critical); }
                .step-dot.indigo { background: var(--accent-primary); }
                .step-dot.success { background: var(--status-success); }
                
                .step-content { flex: 1; }
                .step-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 4px;
                }
                .step-label { font-weight: 700; color: var(--text-primary); font-size: 0.9rem; }
                .step-time { font-size: 0.75rem; color: var(--text-muted); }
                .step-desc { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; }
                
                .status-panel { padding: 24px; display: flex; flex-direction: column; gap: 20px; position: sticky; top: 100px; }
                .panel-title { font-size: 1rem; font-weight: 700; }
                .summary-datum { display: flex; flex-direction: column; gap: 2px; }
                .highlight { 
                    background: var(--surface-hover); 
                    padding: 16px; 
                    border-radius: var(--radius-sm); 
                }
                .datum-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
                .datum-value { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
                .indigo-text { color: var(--accent-primary); }
                .datum-sub { font-size: 0.75rem; color: var(--text-muted); }
                
                .btn-refresh {
                    padding: 10px;
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    border: 1px solid var(--border-color);
                    transition: var(--transition-base);
                }
                .btn-refresh:hover { background: var(--surface-hover); border-color: var(--text-primary); }
                
                .btn-source {
                    display: block;
                    text-align: center;
                    padding: 10px;
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    text-decoration: none;
                    color: var(--text-muted);
                    border: 1px solid var(--border-color);
                    transition: var(--transition-base);
                }
                .btn-source:hover { 
                    background: var(--surface-hover); 
                    color: var(--accent-primary);
                    border-color: var(--accent-primary);
                }

                @media (max-width: 1100px) {
                    .detail-grid { grid-template-columns: 1fr; }
                    .details-sidebar { position: static; }
                }
                @media (max-width: 768px) {
                    .outage-detail-container { padding: 20px; }
                    .hero-section { padding: 24px; }
                    .meta-info-grid { grid-template-columns: 1fr; }
                    .detail-title { font-size: 1.4rem; }
                }
            `}</style>
        </div>
    );
}
