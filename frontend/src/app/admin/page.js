"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";

export default function AdminPage() {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [scrapers, setScrapers] = useState([]);
    const [reports, setReports] = useState([]);
    const [outages, setOutages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [outagesLoading, setOutagesLoading] = useState(false);
    const [editingOutage, setEditingOutage] = useState(null);
    const [editForm, setEditForm] = useState({});
    const [searchQuery, setSearchQuery] = useState("");
    const [filterOperator, setFilterOperator] = useState("");
    const [filterStatus, setFilterStatus] = useState("");
    const [mounted, setMounted] = useState(false);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const PAGE_SIZE = 100;
    const searchTimerRef = useRef(null);

    const fetchOutages = useCallback(async (currentPage = 0, search = searchQuery, operator = filterOperator, status = filterStatus) => {
        setOutagesLoading(true);
        try {
            const params = {
                limit: PAGE_SIZE,
                offset: currentPage * PAGE_SIZE,
            };
            if (search) params.search = search;
            if (operator) params.operator = operator;
            if (status) params.status = status;
            const data = await api.admin.outages.list(params);
            setOutages(data);
            setHasMore(data.length === PAGE_SIZE);
        } catch (err) {
            console.error("Failed to fetch outages:", err);
        } finally {
            setOutagesLoading(false);
        }
    }, []);

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

    const handleFilterChange = (newSearch, newOperator, newStatus) => {
        setPage(0);
        fetchOutages(0, newSearch, newOperator, newStatus);
    };

    useEffect(() => {
        setMounted(true);
        fetchData();
        fetchOutages(0);
    }, []);

    useEffect(() => {
        if (editingOutage) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => { document.body.style.overflow = 'unset'; };
    }, [editingOutage]);


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

    const startEditing = (outage) => {
        setEditingOutage(outage);
        setEditForm({
            incident_id: outage.incident_id || "",
            operator_id: outage.operator_id || "",
            region_id: outage.region_id || "",
            raw_data_id: outage.raw_data_id || "",
            title_sv: outage.title?.sv || "",
            title_en: outage.title?.en || "",
            description_sv: outage.description?.sv || "",
            description_en: outage.description?.en || "",
            status: outage.status,
            severity: outage.severity || "unknown",
            start_time: outage.start_time ? new Date(outage.start_time).toISOString().slice(0, 16) : "",
            end_time: outage.end_time ? new Date(outage.end_time).toISOString().slice(0, 16) : "",
            estimated_fix_time: outage.estimated_fix_time ? new Date(outage.estimated_fix_time).toISOString().slice(0, 16) : "",
            latitude: outage.latitude || "",
            longitude: outage.longitude || "",
            location: outage.location || "",
            affected_services: outage.affected_services || [],
        });
    };

    const handleUpdateOutage = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                incident_id: editForm.incident_id,
                operator_id: editForm.operator_id ? parseInt(editForm.operator_id) : null,
                region_id: editForm.region_id ? parseInt(editForm.region_id) : null,
                raw_data_id: editForm.raw_data_id ? parseInt(editForm.raw_data_id) : null,
                title: { sv: editForm.title_sv, en: editForm.title_en },
                description: { sv: editForm.description_sv, en: editForm.description_en },
                status: editForm.status,
                severity: editForm.severity,
                start_time: editForm.start_time || null,
                end_time: editForm.end_time || null,
                estimated_fix_time: editForm.estimated_fix_time || null,
                latitude: editForm.latitude ? parseFloat(editForm.latitude) : null,
                longitude: editForm.longitude ? parseFloat(editForm.longitude) : null,
                location: editForm.location,
                affected_services: editForm.affected_services,
            };
            await api.admin.outages.update(editingOutage.id, payload);
            addToast(lang === "sv" ? "Driftstörning uppdaterad" : "Outage updated", "success");
            setEditingOutage(null);
            fetchOutages(page, searchQuery, filterOperator, filterStatus);
        } catch (err) {
            addToast(lang === "sv" ? "Kunde inte uppdatera" : "Failed to update", "error");
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
                                        <td className="date-cell">
                                            {r.created_at ? new Date(r.created_at).toLocaleDateString() : "-"}
                                        </td>
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

            <section className="admin-section">
                <div className="section-header-row">
                    <h2 className="section-title font-heading" style={{ marginBottom: 0 }}>{lang === "sv" ? "Hantera driftstörningar" : "Outage Management"}</h2>

                    <div className="filter-controls">
                        <input
                            type="text"
                            placeholder={lang === "sv" ? "Sök (ID, Titel, Plats)..." : "Search (ID, Title, Location)..."}
                            value={searchQuery}
                            onChange={(e) => {
                                const val = e.target.value;
                                setSearchQuery(val);
                                clearTimeout(searchTimerRef.current);
                                searchTimerRef.current = setTimeout(() => {
                                    handleFilterChange(val, filterOperator, filterStatus);
                                }, 400);
                            }}
                            className="search-input"
                        />
                        <select
                            value={filterOperator}
                            onChange={(e) => { setFilterOperator(e.target.value); handleFilterChange(searchQuery, e.target.value, filterStatus); }}
                            className="filter-select"
                        >
                            <option value="">{lang === "sv" ? "Alla operatörer" : "All Operators"}</option>
                            <option value="telia">Telia</option>
                            <option value="tele2">Tele2</option>
                            <option value="telenor">Telenor</option>
                            <option value="tre">Tre</option>
                        </select>
                        <select
                            value={filterStatus}
                            onChange={(e) => { setFilterStatus(e.target.value); handleFilterChange(searchQuery, filterOperator, e.target.value); }}
                            className="filter-select"
                        >
                            <option value="">{lang === "sv" ? "Alla statusar" : "All Statuses"}</option>
                            <option value="active">Active</option>
                            <option value="resolved">Resolved</option>
                            <option value="investigating">Investigating</option>
                            <option value="scheduled">Scheduled</option>
                        </select>
                    </div>
                </div>
                <div className="premium-card table-card" style={{ marginTop: '20px' }}>
                    <div className="table-wrapper custom-scrollbar">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                                    <th>{lang === "sv" ? "Titel" : "Title"}</th>
                                    <th>{lang === "sv" ? "Status" : "Status"}</th>
                                    <th>{lang === "sv" ? "Position" : "Coordinates"}</th>
                                    <th>{lang === "sv" ? "Åtgärd" : "Actions"}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {outagesLoading ? (
                                    <tr>
                                        <td colSpan="6" style={{ textAlign: "center", padding: "2rem" }}>
                                            <div className="loading-spinner" style={{ margin: "0 auto" }}></div>
                                        </td>
                                    </tr>
                                ) : outages.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" style={{ textAlign: "center", padding: "2rem" }}>
                                            {lang === "sv" ? "Inga driftstörningar hittades" : "No outages found"}
                                        </td>
                                    </tr>
                                ) : (
                                    outages.map((o) => (
                                        <tr key={o.id}>
                                            <td className="id-cell">#{o.id}</td>
                                            <td className="op-cell">{o.operator_name}</td>
                                            <td className="title-cell">{o.title[lang] || o.title['sv']}</td>
                                            <td>
                                                <span className={`status-badge-mini ${o.status}`}>
                                                    {o.status}
                                                </span>
                                            </td>
                                            <td className="coord-cell">
                                                {o.latitude ? `${o.latitude.toFixed(4)}, ${o.longitude.toFixed(4)}` : "-"}
                                            </td>
                                            <td className="actions-cell">
                                                <button onClick={() => startEditing(o)} className="btn-edit">
                                                    {lang === "sv" ? "Redigera" : "Edit"}
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '15px', padding: '10px 0' }}>
                        <button
                            className="btn-secondary"
                            disabled={page === 0 || outagesLoading}
                            onClick={() => {
                                const newPage = page - 1;
                                setPage(newPage);
                                fetchOutages(newPage);
                            }}
                        >
                            {lang === "sv" ? "← Föregående" : "← Previous"}
                        </button>
                        <span style={{ alignSelf: 'center', opacity: 0.7 }}>
                            {lang === "sv" ? `Sida ${page + 1}` : `Page ${page + 1}`}
                        </span>
                        <button
                            className="btn-secondary"
                            disabled={!hasMore || outagesLoading}
                            onClick={() => {
                                const newPage = page + 1;
                                setPage(newPage);
                                fetchOutages(newPage);
                            }}
                        >
                            {lang === "sv" ? "Nästa →" : "Next →"}
                        </button>
                    </div>
                </div>
            </section>

            {mounted && editingOutage && createPortal(
                <div className="modal-overlay">
                    <div className="premium-card modal-content animate-slide-up">
                        <header className="modal-header">
                            <h3>{lang === "sv" ? "Redigera driftstörning" : "Edit Outage"} #{editingOutage.id}</h3>
                            <button className="close-btn" onClick={() => setEditingOutage(null)}>×</button>
                        </header>
                        <form onSubmit={handleUpdateOutage} className="edit-form">
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Incident ID</label>
                                    <input value={editForm.incident_id} onChange={e => setEditForm({ ...editForm, incident_id: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Operator ID</label>
                                    <input type="number" value={editForm.operator_id} onChange={e => setEditForm({ ...editForm, operator_id: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Region ID</label>
                                    <input type="number" value={editForm.region_id} onChange={e => setEditForm({ ...editForm, region_id: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Raw Data ID</label>
                                    <input type="number" value={editForm.raw_data_id} onChange={e => setEditForm({ ...editForm, raw_data_id: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Title (Svenska)</label>
                                    <input value={editForm.title_sv} onChange={e => setEditForm({ ...editForm, title_sv: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Title (English)</label>
                                    <input value={editForm.title_en} onChange={e => setEditForm({ ...editForm, title_en: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Description (Svenska)</label>
                                <textarea value={editForm.description_sv} onChange={e => setEditForm({ ...editForm, description_sv: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Description (English)</label>
                                <textarea value={editForm.description_en} onChange={e => setEditForm({ ...editForm, description_en: e.target.value })} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Status</label>
                                    <select value={editForm.status} onChange={e => setEditForm({ ...editForm, status: e.target.value })}>
                                        <option value="detecting">Detecting</option>
                                        <option value="active">Active</option>
                                        <option value="investigating">Investigating</option>
                                        <option value="identified">Identified</option>
                                        <option value="monitoring">Monitoring</option>
                                        <option value="resolved">Resolved</option>
                                        <option value="scheduled">Scheduled</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Severity</label>
                                    <select value={editForm.severity} onChange={e => setEditForm({ ...editForm, severity: e.target.value })}>
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="critical">Critical</option>
                                        <option value="unknown">Unknown</option>
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Start Time</label>
                                    <input type="datetime-local" value={editForm.start_time} onChange={e => setEditForm({ ...editForm, start_time: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>End Time</label>
                                    <input type="datetime-local" value={editForm.end_time} onChange={e => setEditForm({ ...editForm, end_time: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Estimated Fix Time</label>
                                <input type="datetime-local" value={editForm.estimated_fix_time} onChange={e => setEditForm({ ...editForm, estimated_fix_time: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Location Name</label>
                                <input value={editForm.location} onChange={e => setEditForm({ ...editForm, location: e.target.value })} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Latitude</label>
                                    <input type="number" step="any" value={editForm.latitude} onChange={e => setEditForm({ ...editForm, latitude: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Longitude</label>
                                    <input type="number" step="any" value={editForm.longitude} onChange={e => setEditForm({ ...editForm, longitude: e.target.value })} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>{lang === "sv" ? "Påverkade Tjänster" : "Affected Services"}</label>
                                <div className="checkbox-group">
                                    {["5g+", "5g", "4g", "3g", "2g"].map(service => (
                                        <label key={service} className="checkbox-label">
                                            <input
                                                type="checkbox"
                                                checked={editForm.affected_services.includes(service)}
                                                onChange={(e) => {
                                                    const current = new Set(editForm.affected_services);
                                                    if (e.target.checked) current.add(service);
                                                    else current.delete(service);
                                                    setEditForm({ ...editForm, affected_services: Array.from(current) });
                                                }}
                                            />
                                            {service}
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <footer className="modal-footer">
                                <button type="button" className="btn-secondary" onClick={() => setEditingOutage(null)}>Cancel</button>
                                <button type="submit" className="btn-primary">Save Changes</button>
                            </footer>
                        </form>
                    </div>
                </div>,
                document.body
            )}

            <style jsx>{`
                .admin-container { padding: 32px; max-width: 1200px; margin: 0 auto; }
                .admin-header { margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--border-color); }
                .admin-header h1 { font-size: 1.8rem; margin-bottom: 4px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }
                .admin-section { margin-bottom: 48px; }
                .section-header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; }
                .filter-controls { display: flex; gap: 12px; flex-wrap: wrap; }
                .search-input { padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--surface-primary); color: var(--text-primary); font-size: 0.9rem; min-width: 250px; }
                .filter-select { padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--surface-primary); color: var(--text-primary); font-size: 0.9rem; cursor: pointer; }
                .section-title { margin-bottom: 20px; font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
                .scraper-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
                .scraper-card { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
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
                .admin-table th { padding: 14px 20px; background: var(--surface-hover); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-weight: 700; border-bottom: 1px solid var(--border-color); }
                .admin-table td { padding: 14px 20px; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; }
                .op-cell { font-weight: 700; color: var(--accent-primary); }
                .id-cell { font-family: monospace; color: var(--text-muted); font-size: 0.75rem; }
                .status-badge-mini { padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
                .status-badge-mini.active { border: 1px solid var(--status-success); color: var(--status-success); }
                .status-badge-mini.pending { background: var(--surface-hover); color: var(--status-warning); border: 1px solid var(--border-color); }
                .status-badge-mini.verified { border: 1px solid var(--status-success); color: var(--status-success); }
                .status-badge-mini.rejected { border: 1px solid var(--status-critical); color: var(--status-critical); }
                .action-btns { display: flex; gap: 8px; }
                .action-btns button, .btn-edit { padding: 4px 10px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--border-color); background: transparent; cursor: pointer; transition: all 0.2s; }
                .btn-edit:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
                .btn-verify:hover { border-color: var(--status-success); color: var(--status-success); }
                .btn-reject:hover { border-color: var(--status-critical); color: var(--status-critical); }
                
                /* Modal Styles */
                .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
                .modal-content { width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto; background: var(--surface-primary); border: 1px solid var(--border-color); }
                .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border-color); }
                .close-btn { background: none; border: none; font-size: 1.5rem; color: var(--text-muted); cursor: pointer; }
                .edit-form { padding: 24px; }
                .form-group { margin-bottom: 16px; display: flex; flex-direction: column; gap: 6px; }
                .form-group label { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
                .form-group input, .form-group textarea, .form-group select { padding: 10px 12px; border-radius: 6px; background: var(--surface-hover); border: 1px solid var(--border-color); color: var(--text-primary); font-size: 0.9rem; }
                .form-group textarea { min-height: 80px; resize: vertical; }
                .checkbox-group { display: flex; gap: 16px; flex-wrap: wrap; padding: 8px 0; }
                .checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: var(--text-primary); cursor: pointer; text-transform: none !important; font-weight: normal !important; }
                .checkbox-label input { width: 16px; height: 16px; margin: 0; cursor: pointer; }
                .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
                .modal-footer { margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px; }
                .btn-primary { background: var(--accent-primary) !important; color: white !important; border: none !important; padding: 10px 20px !important; border-radius: 6px !important; cursor: pointer; font-weight: 700; }
                .btn-secondary { background: var(--surface-hover) !important; color: var(--text-primary) !important; border: 1px solid var(--border-color) !important; padding: 10px 20px !important; border-radius: 6px !important; cursor: pointer; }

                @media (max-width: 768px) { .admin-container { padding: 20px; } .scraper-grid { grid-template-columns: 1fr; } .form-row { grid-template-columns: 1fr; } }
            `}</style>
        </div>
    );
}
