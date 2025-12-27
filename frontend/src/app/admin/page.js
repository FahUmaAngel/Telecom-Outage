"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";

export default function AdminPage() {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [scrapers, setScrapers] = useState([]);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [scrapersData, reportsData] = await Promise.all([
                api.admin.scrapers(),
                api.admin.reports.list(),
            ]);
            setScrapers(scrapersData);
            setReports(reportsData);
        } catch (err) {
            console.error("Failed to fetch admin data:", err);
            addToast(lang === "sv" ? "Kunde inte hämta admin-data" : "Failed to fetch admin data", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleReportAction = async (id, action) => {
        try {
            if (action === "verify") {
                await api.admin.reports.verify(id);
            } else {
                await api.admin.reports.reject(id);
            }
            addToast(lang === "sv" ? "Rapport uppdaterad" : "Report updated", "success");
            fetchData();
        } catch (err) {
            addToast(lang === "sv" ? "Kunde ikke uppdatera rapport" : "Failed to update report", "error");
        }
    };

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div className="admin-container animate-fade-in">
            <header className="admin-header">
                <h1 className="text-gradient">
                    {lang === "sv" ? "Administration" : "Admin Control Panel"}
                </h1>
                <p className="subtitle">
                    {lang === "sv" ? "Systemövervakning och moderering" : "System monitoring and moderation"}
                </p>
            </header>

            <section className="admin-section">
                <h2 className="section-title font-heading">{lang === "sv" ? "Scraper-status" : "Scraper Health"}</h2>
                <div className="scraper-grid">
                    {scrapers.map((s) => (
                        <div key={s.operator} className="premium-card scraper-card">
                            <div className="scraper-main">
                                <div className={`status-dot ${new Date() - new Date(s.last_scraped_at) < 3600000 ? 'online' : 'stale'}`}></div>
                                <div className="scraper-info">
                                    <span className="operator-name">{s.operator.toUpperCase()}</span>
                                    <span className="last-scrape">
                                        {lang === "sv" ? "Senaste: " : "Last Sync: "}
                                        {new Date(s.last_scraped_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                            </div>
                            <div className="scraper-date">
                                {new Date(s.last_scraped_at).toLocaleDateString()}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="admin-section">
                <h2 className="section-title font-heading">{lang === "sv" ? "Ärendehantering" : "User Report Moderation"}</h2>
                <div className="premium-card table-card">
                    <div className="table-wrapper custom-scrollbar">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                                    <th>{lang === "sv" ? "Ärende" : "Title"}</th>
                                    <th>{lang === "sv" ? "Status" : "Status"}</th>
                                    <th>{lang === "sv" ? "Datum" : "Date"}</th>
                                    <th>{lang === "sv" ? "Åtgärd" : "Actions"}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reports.map((r) => (
                                    <tr key={r.id}>
                                        <td className="op-cell">{r.operator_name || "General"}</td>
                                        <td className="title-cell">{r.title}</td>
                                        <td>
                                            <span className={`status-badge-mini ${r.status}`}>
                                                {r.status}
                                            </span>
                                        </td>
                                        <td className="date-cell">{new Date(r.created_at).toLocaleDateString()}</td>
                                        <td className="actions-cell">
                                            {r.status === "pending" ? (
                                                <div className="action-btns">
                                                    <button onClick={() => handleReportAction(r.id, "verify")} className="btn-verify">Verify</button>
                                                    <button onClick={() => handleReportAction(r.id, "reject")} className="btn-reject">Reject</button>
                                                </div>
                                            ) : (
                                                <span className="processed-label">Processed</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <style jsx>{`
                .admin-container {
                    padding: 32px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .admin-header { 
                    margin-bottom: 40px; 
                    padding-bottom: 24px;
                    border-bottom: 1px solid var(--border-color);
                }
                .admin-header h1 { font-size: 1.8rem; margin-bottom: 4px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }
                
                .admin-section { margin-bottom: 48px; }
                .section-title { margin-bottom: 20px; font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }

                .scraper-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                    gap: 16px;
                }
                .scraper-card {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                }
                .scraper-main { display: flex; align-items: center; gap: 12px; }
                .status-dot { width: 6px; height: 6px; border-radius: 50%; }
                .online { background: var(--status-success); }
                .stale { background: var(--status-warning); }
                
                .operator-name { font-weight: 700; font-size: 0.95rem; color: var(--text-primary); }
                .last-scrape { font-size: 0.8rem; color: var(--text-muted); display: block; }
                .scraper-date { font-size: 0.8rem; color: var(--text-muted); }

                .table-card { padding: 0; overflow: hidden; }
                .table-wrapper { overflow-x: auto; }
                .admin-table { width: 100%; border-collapse: collapse; text-align: left; }
                .admin-table th { 
                    padding: 14px 20px; 
                    background: var(--surface-hover);
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: var(--text-muted);
                    font-weight: 700;
                    border-bottom: 1px solid var(--border-color);
                }
                .admin-table td { 
                    padding: 14px 20px; 
                    border-bottom: 1px solid var(--border-color);
                    font-size: 0.85rem;
                }
                .op-cell { font-weight: 700; color: var(--accent-primary); }
                
                .status-badge-mini {
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.65rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.02em;
                }
                .status-badge-mini.pending { background: var(--surface-hover); color: var(--status-warning); border: 1px solid var(--border-color); }
                .status-badge-mini.verified { border: 1px solid var(--status-success); color: var(--status-success); }
                .status-badge-mini.rejected { border: 1px solid var(--status-critical); color: var(--status-critical); }

                .action-btns { display: flex; gap: 8px; }
                .action-btns button {
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    border: 1px solid var(--border-color);
                }
                .btn-verify:hover { border-color: var(--status-success); color: var(--status-success); }
                .btn-reject:hover { border-color: var(--status-critical); color: var(--status-critical); }
                .processed-label { font-size: 0.75rem; color: var(--text-muted); font-style: italic; }

                @media (max-width: 768px) {
                    .admin-container { padding: 20px; }
                    .scraper-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
