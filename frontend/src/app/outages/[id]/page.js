"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useLanguage } from "../../../context/LanguageContext";
import { api } from "../../../lib/api";
import {
    AlertCircle,
    Calendar,
    Clock,
    CheckCircle2,
    Activity,
    MapPin,
    ShieldAlert,
    ChevronLeft,
    Wrench,
    ArrowRight
} from "lucide-react";

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
                <AlertCircle size={48} className="error-icon" />
                <h2>{error || (lang === "sv" ? "Avbrottet hittades inte" : "Outage not found")}</h2>
                <button onClick={() => router.back()} className="back-btn">
                    {lang === "sv" ? "Gå tillbaka" : "Go back"}
                </button>
                <style jsx>{`
                    .error-state {
                        padding: 60px 40px;
                        text-align: center;
                        margin-top: 50px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 20px;
                    }
                    .error-icon { color: var(--status-critical); opacity: 0.8; }
                    .back-btn {
                        padding: 10px 24px;
                        background: var(--accent-primary);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-weight: 700;
                        cursor: pointer;
                        transition: var(--transition-base);
                    }
                    .back-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
                `}</style>
            </div>
        );
    }

    const isResolved = outage.status.toLowerCase() === "resolved";
    const hasEstimation = !!outage.estimated_fix_time;
    const hasUpdates = outage.updated_at && new Date(outage.updated_at) > new Date(outage.start_time);

    return (
        <div className="outage-detail-container animate-fade-in">
            <header className="detail-header">
                <Link href="/" className="back-link">
                    <ChevronLeft size={18} /> {lang === "sv" ? "Dashboard" : "Dashboard"}
                </Link>
                <div className={`status-badge-detail status-${outage.status.toLowerCase()}`}>
                    <span className="dot"></span>
                    {outage.status}
                </div>
            </header>

            <div className="detail-grid">
                <div className="main-column">
                    <section className="premium-card hero-section">
                        <div className="operator-chip">
                            {outage.operator_name}
                        </div>
                        <h1 className="detail-title">{t(outage.title)}</h1>

                        <div className="meta-info-grid">
                            <div className="info-item">
                                <div className="info-header">
                                    <MapPin size={14} />
                                    <span className="info-label">{lang === "sv" ? "Plats" : "Location"}</span>
                                </div>
                                <span className="info-value">{outage.location || "Sweden"}</span>
                            </div>
                            <div className="info-item">
                                <div className="info-header">
                                    <ShieldAlert size={14} />
                                    <span className="info-label">{lang === "sv" ? "Allvarlighetsgrad" : "Severity"}</span>
                                </div>
                                <span className={`info-value severity-${outage.severity.toLowerCase()}`}>
                                    {outage.severity}
                                </span>
                            </div>
                            <div className="info-item">
                                <div className="info-header">
                                    <Clock size={14} />
                                    <span className="info-label">{lang === "sv" ? "Starttid" : "Started"}</span>
                                </div>
                                <span className="info-value">
                                    {outage.start_time ? new Date(outage.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : "-"}
                                </span>
                            </div>
                            <div className="info-item">
                                <div className="info-header">
                                    <Activity size={14} />
                                    <span className="info-label">{lang === "sv" ? "Status" : "Status"}</span>
                                </div>
                                <span className="info-value">{outage.status}</span>
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
                        <h3 className="section-title">{lang === "sv" ? "Incidentförlopp" : "Incident Timeline"}</h3>
                        <div className="visual-timeline">
                            {/* Step 1: Detected */}
                            <div className={`timeline-node completed`}>
                                <div className="node-marker">
                                    <AlertCircle size={16} />
                                </div>
                                <div className="node-content">
                                    <div className="node-header">
                                        <span className="node-title">{lang === "sv" ? "Problem identifierat" : "Issue Detected"}</span>
                                        <span className="node-time">{new Date(outage.start_time).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="node-desc">{lang === "sv" ? `Avbrott rapporterat hos ${outage.operator_name}` : `Outage reported at ${outage.operator_name}`}</p>
                                </div>
                            </div>

                            {/* Step 2: Investigation / Updates */}
                            <div className={`timeline-node ${hasUpdates || isResolved ? 'completed' : 'active'}`}>
                                <div className="node-marker">
                                    <Activity size={16} />
                                </div>
                                <div className="node-content">
                                    <div className="node-header">
                                        <span className="node-title">{lang === "sv" ? "Undersökning pågår" : "Investigation"}</span>
                                        {hasUpdates && <span className="node-time">{new Date(outage.updated_at).toLocaleTimeString()}</span>}
                                    </div>
                                    <p className="node-desc">{lang === "sv" ? "Tekniker analyserar omfattningen och förbereder åtgärder." : "Engineers are analyzing the impact and preparing repairs."}</p>
                                </div>
                            </div>

                            {/* Step 3: ETA / Fix Scheduled (Optional) */}
                            {hasEstimation && (
                                <div className={`timeline-node ${isResolved ? 'completed' : 'active'}`}>
                                    <div className="node-marker highlight">
                                        <Wrench size={16} />
                                    </div>
                                    <div className="node-content">
                                        <div className="node-header">
                                            <span className="node-title">{lang === "sv" ? "Åtgärd planerad" : "Fix Scheduled"}</span>
                                            <span className="node-time">{new Date(outage.estimated_fix_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        </div>
                                        <p className="node-desc">{lang === "sv" ? "Beräknad tid för lösning är satt." : "Estimated time for resolution has been confirmed."}</p>
                                    </div>
                                </div>
                            )}

                            {/* Step 4: Resolved */}
                            <div className={`timeline-node ${isResolved ? 'completed resolved' : 'pending'}`}>
                                <div className="node-marker">
                                    <CheckCircle2 size={16} />
                                </div>
                                <div className="node-content">
                                    <div className="node-header">
                                        <span className="node-title">{lang === "sv" ? "Återställt" : "Resolution"}</span>
                                        {isResolved && <span className="node-time">{outage.end_time ? new Date(outage.end_time).toLocaleTimeString() : new Date(outage.updated_at).toLocaleTimeString()}</span>}
                                    </div>
                                    <p className="node-desc">{isResolved ? (lang === "sv" ? "Tjänsterna är nu fullt återställda." : "All services have been fully restored.") : (lang === "sv" ? "Väntarบน verifiering." : "Awaiting final verification.")}</p>
                                </div>
                            </div>
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
                    padding: 40px 32px;
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
                    font-size: 0.8rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    transition: var(--transition-base);
                }
                .back-link:hover { color: var(--accent-primary); }
                
                .status-badge-detail {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-weight: 800;
                    text-transform: uppercase;
                    font-size: 0.65rem;
                    letter-spacing: 0.08em;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                }
                .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
                .status-active { color: var(--status-critical); border-color: rgba(var(--status-critical-rgb), 0.3); }
                .status-active .dot { animation: pulse 2s infinite; }
                .status-resolved { color: var(--status-success); border-color: rgba(var(--status-success-rgb), 0.3); }

                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.5); opacity: 0.5; }
                    100% { transform: scale(1); opacity: 1; }
                }

                .detail-grid {
                    display: grid;
                    grid-template-columns: 1fr 340px;
                    gap: 32px;
                }
                
                .hero-section { padding: 40px; margin-bottom: 24px; position: relative; overflow: hidden; }
                .operator-chip {
                    display: inline-block;
                    padding: 4px 12px;
                    background: var(--accent-glow);
                    color: var(--accent-primary);
                    border-radius: 6px;
                    font-weight: 800;
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    margin-bottom: 16px;
                }
                .detail-title { font-size: 2rem; margin-bottom: 40px; font-weight: 800; line-height: 1.2; }
                
                .meta-info-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 24px;
                    margin-bottom: 40px;
                    padding: 32px;
                    background: var(--surface-hover);
                    border-radius: var(--radius-lg);
                    border: 1px solid var(--border-color);
                }
                .info-item { display: flex; flex-direction: column; gap: 8px; }
                .info-header { display: flex; align-items: center; gap: 8px; color: var(--text-muted); }
                .info-label { font-size: 0.7rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
                .info-value { font-size: 1.05rem; font-weight: 700; color: var(--text-primary); }
                
                .severity-critical { color: var(--status-critical); }
                
                .sub-title { font-size: 0.85rem; font-weight: 800; margin-bottom: 16px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; }
                .description-text { line-height: 1.7; color: var(--text-secondary); font-size: 1rem; }
                
                .description-section { margin-top: 40px; }
                .services-section { margin-top: 40px; padding-top: 32px; border-top: 1px solid var(--border-color); }
                .service-list { display: flex; gap: 10px; flex-wrap: wrap; }
                .service-tag {
                    padding: 6px 14px;
                    border-radius: 8px;
                    font-size: 0.8rem;
                    font-weight: 700;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                    color: var(--text-secondary);
                }

                .history-section { padding: 40px; }
                .section-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 32px; }
                
                /* Visual Timeline Component */
                .visual-timeline { display: flex; flex-direction: column; gap: 0; }
                .timeline-node {
                    display: flex;
                    gap: 24px;
                    padding-bottom: 40px;
                    position: relative;
                }
                .timeline-node:not(:last-child)::after {
                    content: '';
                    position: absolute;
                    left: 15px;
                    top: 32px;
                    bottom: 0;
                    width: 2px;
                    background: var(--border-color);
                }
                .timeline-node.completed:not(:last-child)::after {
                    background: var(--accent-primary);
                }
                .timeline-node.resolved:not(:last-child)::after {
                    background: var(--status-success);
                }

                .node-marker {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: var(--surface-color);
                    border: 2px solid var(--border-color);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    z-index: 1;
                    color: var(--text-muted);
                    transition: var(--transition-base);
                }
                .timeline-node.completed .node-marker {
                    background: var(--accent-primary);
                    border-color: var(--accent-primary);
                    color: white;
                    box-shadow: 0 0 15px var(--accent-glow);
                }
                .timeline-node.resolved .node-marker {
                    background: var(--status-success);
                    border-color: var(--status-success);
                }
                .timeline-node.active .node-marker {
                    border-color: var(--accent-primary);
                    color: var(--accent-primary);
                    animation: pulse-border 2s infinite;
                }
                .node-marker.highlight { background: var(--surface-hover); border-style: dashed; }

                @keyframes pulse-border {
                    0% { box-shadow: 0 0 0 0 var(--accent-glow); }
                    70% { box-shadow: 0 0 0 10px rgba(var(--accent-primary-rgb), 0); }
                    100% { box-shadow: 0 0 0 0 rgba(var(--accent-primary-rgb), 0); }
                }

                .node-content { flex: 1; padding-top: 4px; }
                .node-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 6px;
                }
                .node-title { font-weight: 800; color: var(--text-primary); font-size: 0.95rem; }
                .node-time { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; }
                .node-desc { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; }
                
                .timeline-node.pending { opacity: 0.5; }
                
                .status-panel { padding: 32px; display: flex; flex-direction: column; gap: 24px; position: sticky; top: 100px; }
                .panel-title { font-size: 1.1rem; font-weight: 800; }
                .summary-datum { display: flex; flex-direction: column; gap: 4px; }
                .highlight { 
                    background: var(--surface-hover); 
                    padding: 20px; 
                    border-radius: var(--radius-md); 
                    border-left: 4px solid var(--accent-primary);
                }
                .datum-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
                .datum-value { font-size: 1.2rem; font-weight: 800; color: var(--text-primary); }
                .indigo-text { color: var(--accent-primary); }
                .datum-sub { font-size: 0.8rem; color: var(--text-muted); }
                
                .btn-refresh {
                    padding: 12px;
                    border-radius: 8px;
                    font-weight: 800;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    background: transparent;
                    border: 1px solid var(--border-color);
                    color: var(--text-primary);
                    cursor: pointer;
                    transition: var(--transition-base);
                }
                .btn-refresh:hover { background: var(--surface-hover); border-color: var(--text-primary); }
                
                .btn-source {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 12px;
                    border-radius: 8px;
                    font-weight: 800;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
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
                    .status-panel { position: static; }
                }
                @media (max-width: 768px) {
                    .outage-detail-container { padding: 20px; }
                    .hero-section { padding: 24px; }
                    .meta-info-grid { grid-template-columns: 1fr; padding: 20px; }
                    .detail-title { font-size: 1.5rem; }
                }
            `}</style>
        </div>
    );
}
