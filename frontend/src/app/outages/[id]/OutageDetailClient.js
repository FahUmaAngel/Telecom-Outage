"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useLanguage } from "../../../context/LanguageContext";
import { api } from "../../../lib/api";
import {
    AlertCircle,
    Clock,
    CheckCircle2,
    Activity,
    MapPin,
    ShieldAlert,
    ChevronLeft,
    Wrench
} from "lucide-react";
import PropTypes from "prop-types";

const LoadingState = () => (
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

const ErrorState = ({ error, lang, onBack }) => (
    <div className="error-state glass">
        <AlertCircle size={48} className="error-icon" />
        <h2>{error || (lang === "sv" ? "Avbrottet hittades inte" : "Outage not found")}</h2>
        <button onClick={onBack} className="back-btn">
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

ErrorState.propTypes = {
    error: PropTypes.string,
    lang: PropTypes.string.isRequired,
    onBack: PropTypes.func.isRequired
};

const OutageTimeline = ({ outage, lang, hasUpdates, isResolved, hasEstimation, resolutionDesc }) => (
    <section className="premium-card history-section">
        <h3 className="section-title">{lang === "sv" ? "Incidentförlopp" : "Incident Timeline"}</h3>
        <div className="visual-timeline">
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

            {hasEstimation && (
                <div className={`timeline-node ${isResolved ? 'completed' : 'active'}`}>
                    <div className="node-marker highlight">
                        <Wrench size={16} />
                    </div>
                    <div className="node-content">
                        <div className="node-header">
                            <span className="node-title">{lang === "sv" ? "Åtgärd planerad" : "Fix Scheduled"}</span>
                            <span className="node-time">{new Date(outage.estimated_fix_time).toLocaleTimeString()}</span>
                        </div>
                        <p className="node-desc">{lang === "sv" ? "Beräknad återställningstid enligt operatören." : "Estimated restoration time provided by the operator."}</p>
                    </div>
                </div>
            )}

            <div className={`timeline-node ${isResolved ? 'resolved completed' : 'pending'}`}>
                <div className="node-marker">
                    <CheckCircle2 size={16} />
                </div>
                <div className="node-content">
                    <div className="node-header">
                        <span className="node-title">{lang === "sv" ? "Återställt" : "Resolved"}</span>
                        {isResolved && outage.end_time && <span className="node-time">{new Date(outage.end_time).toLocaleTimeString()}</span>}
                    </div>
                    <p className="node-desc">
                        {isResolved ? (resolutionDesc || (lang === "sv" ? "Incidenten verkar vara åtgärdad." : "The incident appears to be resolved.")) :
                            (lang === "sv" ? "Väntar på att operatören markerar incidenten som löst." : "Waiting for the operator to mark the incident as resolved.")}
                    </p>
                </div>
            </div>
        </div>
    </section>
);

OutageTimeline.propTypes = {
    outage: PropTypes.object.isRequired,
    lang: PropTypes.string.isRequired,
    hasUpdates: PropTypes.bool.isRequired,
    isResolved: PropTypes.bool.isRequired,
    hasEstimation: PropTypes.bool.isRequired,
    resolutionDesc: PropTypes.string
};

export default function OutageDetailClient() {
    const { lang } = useLanguage();
    const params = useParams();
    const router = useRouter();

    const [outage, setOutage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const outageId = params?.id;

    useEffect(() => {
        let mounted = true;
        async function load() {
            if (!outageId) return;
            setLoading(true);
            setError(null);
            try {
                const data = await api.outages.getById(outageId);
                if (!mounted) return;
                setOutage(data);
            } catch (err) {
                if (!mounted) return;
                setError(err?.message || (lang === "sv" ? "Kunde inte hämta avbrottet" : "Failed to load outage"));
            } finally {
                if (mounted) setLoading(false);
            }
        }
        load();
        return () => { mounted = false; };
    }, [outageId, lang]);

    const onBack = () => router.back();

    if (loading) return <LoadingState />;
    if (error || !outage) return <ErrorState error={error} lang={lang} onBack={onBack} />;

    const isResolved = String(outage.status || "").toLowerCase() === "resolved";
    const hasUpdates = outage.updated_at && outage.updated_at !== outage.start_time;
    const hasEstimation = Boolean(outage.estimated_fix_time);
    const resolutionDesc = isResolved ? (lang === "sv" ? "Incidenten är markerad som löst." : "The incident is marked as resolved.") : null;

    return (
        <div className="outage-detail-container animate-fade-in">
            <div className="detail-header">
                <button className="back-link" onClick={onBack}>
                    <ChevronLeft size={18} />
                    {lang === "sv" ? "Tillbaka" : "Back"}
                </button>
                <Link href="/" className="home-link">{lang === "sv" ? "Översikt" : "Overview"}</Link>
            </div>

            <div className="detail-grid">
                <section className="premium-card hero-section">
                    <div className="hero-top">
                        <div className="operator-pill">{outage.operator_name}</div>
                        <div className={`status-pill status-${String(outage.status || "").toLowerCase()}`}>
                            {outage.status}
                        </div>
                    </div>
                    <h1 className="detail-title">{outage.title?.[lang] || outage.title?.sv || outage.title?.en || outage.incident_id}</h1>
                    <p className="detail-desc">{outage.description?.[lang] || outage.description?.sv || outage.description?.en}</p>

                    <div className="meta-info-grid">
                        <div className="meta-item">
                            <Clock size={16} />
                            <div>
                                <div className="meta-label">{lang === "sv" ? "Start" : "Started"}</div>
                                <div className="meta-value">{new Date(outage.start_time).toLocaleString()}</div>
                            </div>
                        </div>
                        <div className="meta-item">
                            <MapPin size={16} />
                            <div>
                                <div className="meta-label">{lang === "sv" ? "Plats" : "Location"}</div>
                                <div className="meta-value">{outage.location || "—"}</div>
                            </div>
                        </div>
                        <div className="meta-item">
                            <ShieldAlert size={16} />
                            <div>
                                <div className="meta-label">{lang === "sv" ? "Allvar" : "Severity"}</div>
                                <div className="meta-value">{outage.severity || "—"}</div>
                            </div>
                        </div>
                    </div>
                </section>

                <div className="detail-main">
                    <OutageTimeline
                        outage={outage}
                        lang={lang}
                        hasUpdates={Boolean(hasUpdates)}
                        isResolved={Boolean(isResolved)}
                        hasEstimation={Boolean(hasEstimation)}
                        resolutionDesc={resolutionDesc}
                    />

                    {outage.source_url && (
                        <section className="premium-card">
                            <h3 className="section-title">{lang === "sv" ? "Källa" : "Source"}</h3>
                            <a className="btn-source" href={outage.source_url} target="_blank" rel="noreferrer">
                                {lang === "sv" ? "Öppna hos operatören" : "Open on operator site"}
                            </a>
                        </section>
                    )}
                </div>
            </div>

            <style jsx>{`
                .outage-detail-container { padding: 40px; max-width: 1200px; margin: 0 auto; }
                .detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
                .back-link {
                    display: inline-flex; align-items: center; gap: 8px;
                    border: 1px solid var(--border-color); background: transparent; color: var(--text-primary);
                    padding: 10px 14px; border-radius: 10px; font-weight: 800; cursor: pointer;
                }
                .home-link { color: var(--text-muted); text-decoration: none; font-weight: 800; }
                .detail-grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
                .hero-section { padding: 28px; }
                .hero-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }
                .operator-pill { font-weight: 900; letter-spacing: 0.04em; color: var(--accent-primary); }
                .status-pill { font-family: monospace; font-weight: 800; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border-color); }
                .detail-title { font-size: 1.9rem; margin: 6px 0 10px; }
                .detail-desc { color: var(--text-secondary); line-height: 1.6; }
                .meta-info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 20px; }
                .meta-item { display: flex; gap: 10px; align-items: flex-start; padding: 12px; border-radius: 12px; background: var(--surface-hover); border: 1px solid var(--border-color); }
                .meta-label { font-size: 0.7rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); }
                .meta-value { font-weight: 800; }
                .detail-main { display: grid; gap: 18px; }
                .section-title { font-weight: 900; margin-bottom: 12px; }
                .btn-source {
                    display: inline-flex; align-items: center; justify-content: center;
                    border: 1px solid var(--border-color); border-radius: 10px;
                    padding: 12px 14px; font-weight: 900; text-decoration: none;
                    color: var(--text-primary); background: transparent;
                }
                .visual-timeline { display: grid; gap: 16px; }
                .timeline-node { display: flex; gap: 14px; }
                .node-marker {
                    width: 34px; height: 34px; border-radius: 999px;
                    display: grid; place-items: center;
                    border: 2px solid var(--border-color); background: var(--surface-color);
                }
                .timeline-node.completed .node-marker { background: var(--accent-primary); border-color: var(--accent-primary); color: white; }
                .timeline-node.resolved .node-marker { background: var(--status-success); border-color: var(--status-success); }
                .timeline-node.active .node-marker { border-color: var(--accent-primary); color: var(--accent-primary); }
                .node-content { flex: 1; }
                .node-header { display: flex; justify-content: space-between; gap: 10px; }
                .node-title { font-weight: 900; }
                .node-time { font-family: monospace; color: var(--text-muted); }
                .node-desc { color: var(--text-secondary); margin-top: 4px; line-height: 1.55; }

                @media (max-width: 900px) {
                    .outage-detail-container { padding: 20px; }
                    .meta-info-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}

