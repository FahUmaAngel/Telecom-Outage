"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";

/**
 * Custom hook for general admin data (scrapers and reports)
 */
function useAdminData() {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [scrapers, setScrapers] = useState([]);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const [scrapersData, reportsData] = await Promise.all([
                api.admin.scrapers(),
                api.admin.reports.list(),
            ]);
            setScrapers(scrapersData);
            setReports(reportsData);
        } catch (err) {
            console.error("Failed to fetch admin data:", err);
            throw err;
        } finally {
            setLoading(false);
        }
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
            console.error(`Failed to ${action} report ${id}:`, err);
            addToast(lang === "sv" ? "Kunde inte uppdatera rapport" : "Failed to update report", "error");
        }
    };

    return { scrapers, reports, loading, fetchData, handleReportAction };
}

/**
 * Custom hook for outage management logic
 */
function useOutageManagement() {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [outages, setOutages] = useState([]);
    const [outagesLoading, setOutagesLoading] = useState(false);
    const [editingOutage, setEditingOutage] = useState(null);
    const [editForm, setEditForm] = useState({});
    const [searchQuery, setSearchQuery] = useState("");
    const [filterOperator, setFilterOperator] = useState("");
    const [filterStatus, setFilterStatus] = useState("");
    const [filterMissingCoords, setFilterMissingCoords] = useState(false);
    const [filterMissingEndDate, setFilterMissingEndDate] = useState(false);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const PAGE_SIZE = 100;
    const searchTimerRef = useRef(null);

    const fetchOutages = useCallback(async (currentPage = 0, search = searchQuery, operator = filterOperator, status = filterStatus, missingCoords = filterMissingCoords, missingEndDate = filterMissingEndDate) => {
        setOutagesLoading(true);
        try {
            const params = {
                limit: PAGE_SIZE,
                offset: currentPage * PAGE_SIZE,
            };
            if (search) params.search = search;
            if (operator) params.operator = operator;
            if (status) params.status = status;
            if (missingCoords) params.missing_coords = true;
            if (missingEndDate) params.missing_end_date = true;
            
            const data = await api.admin.outages.list(params);
            setOutages(data);
            setHasMore(data.length === PAGE_SIZE);
        } catch (err) {
            console.error("Failed to fetch outages:", err);
            addToast(lang === "sv" ? "Kunde inte hämta driftstörningar" : "Failed to fetch outages", "error");
        } finally {
            setOutagesLoading(false);
        }
    }, [searchQuery, filterOperator, filterStatus, filterMissingCoords, filterMissingEndDate, addToast, lang]);

    const handleFilterChange = (
        newSearch = searchQuery,
        newOperator = filterOperator,
        newStatus = filterStatus,
        newMissingCoords = filterMissingCoords,
        newMissingEndDate = filterMissingEndDate,
    ) => {
        setPage(0);
        fetchOutages(0, newSearch, newOperator, newStatus, newMissingCoords, newMissingEndDate);
    };

    const startEditing = (outage) => {
        setEditingOutage(outage);
        const titleSv = outage.title?.sv || "";
        const titleEn = outage.title?.en || "";
        const descSv = outage.description?.sv || "";
        const descEn = outage.description?.en || "";
        const startStr = outage.start_time ? new Date(outage.start_time).toISOString().slice(0, 16) : "";
        const endStr = outage.end_time ? new Date(outage.end_time).toISOString().slice(0, 16) : "";
        const fixStr = outage.estimated_fix_time ? new Date(outage.estimated_fix_time).toISOString().slice(0, 16) : "";
        
        setEditForm({
            incident_id: outage.incident_id || "",
            operator_id: outage.operator_id || "",
            region_id: outage.region_id || "",
            raw_data_id: outage.raw_data_id || "",
            title_sv: titleSv,
            title_en: titleEn,
            description_sv: descSv,
            description_en: descEn,
            status: outage.status,
            severity: outage.severity || "unknown",
            start_time: startStr,
            end_time: endStr,
            estimated_fix_time: fixStr,
            latitude: outage.latitude || "",
            longitude: outage.longitude || "",
            location: outage.location || "",
            place: outage.place || "",
            affected_services: outage.affected_services || [],
        });
    };

    const handleResolvePlace = async () => {
        if (!editForm.place) return;
        try {
            const data = await api.admin.outages.resolvePlace(editForm.place);
            setEditForm(prev => ({
                ...prev,
                latitude: data.latitude,
                longitude: data.longitude,
                location: data.display_name,
                region_id: data.region_id || prev.region_id
            }));
            addToast(lang === "sv" ? "Plats identifierad" : "Place resolved", "success");
        } catch (err) {
            console.error("Failed to resolve place:", err);
            addToast(lang === "sv" ? "Kunde inte hämta platsen" : "Failed to resolve place", "error");
        }
    };

    const handleUpdateOutage = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                incident_id: editForm.incident_id,
                operator_id: editForm.operator_id ? Number.parseInt(editForm.operator_id) : null,
                region_id: editForm.region_id ? Number.parseInt(editForm.region_id) : null,
                raw_data_id: editForm.raw_data_id ? Number.parseInt(editForm.raw_data_id) : null,
                title: { sv: editForm.title_sv, en: editForm.title_en },
                description: { sv: editForm.description_sv, en: editForm.description_en },
                status: editForm.status,
                severity: editForm.severity,
                start_time: editForm.start_time || null,
                end_time: editForm.end_time || null,
                estimated_fix_time: editForm.estimated_fix_time || null,
                latitude: editForm.latitude ? Number.parseFloat(editForm.latitude) : null,
                longitude: editForm.longitude ? Number.parseFloat(editForm.longitude) : null,
                location: editForm.location,
                place: editForm.place,
                affected_services: editForm.affected_services,
            };
            await api.admin.outages.update(editingOutage.id, payload);
            addToast(lang === "sv" ? "Driftstörning uppdaterad" : "Outage updated", "success");
            setEditingOutage(null);
            fetchOutages(page, searchQuery, filterOperator, filterStatus, filterMissingCoords, filterMissingEndDate);
        } catch (err) {
            console.error("Failed to update outage:", err);
            addToast(lang === "sv" ? "Kunde inte uppdatera" : "Failed to update", "error");
        }
    };

    return {
        outages, outagesLoading, editingOutage, editForm, searchQuery, filterOperator, filterStatus,
        filterMissingCoords, filterMissingEndDate, page, hasMore, searchTimerRef,
        setSearchQuery, setFilterOperator, setFilterStatus, setFilterMissingCoords,
        setFilterMissingEndDate, setPage, setEditingOutage, setEditForm,
        fetchOutages, handleFilterChange, startEditing, handleResolvePlace, handleUpdateOutage
    };
}

/**
 * Component for Scraper Health Section
 */
function ScraperHealth({ scrapers, lang }) {
    return (
        <section className="admin-section">
            <h2 className="section-title font-heading">{lang === "sv" ? "Scraper-status" : "Scraper Health"}</h2>
            <div className="scraper-grid">
                {scrapers.filter(s => s.operator !== 'tele2').map((s) => {
                    const isOnline = Date.now() - new Date(s.last_scraped_at).getTime() < 3600000;
                    return (
                    <div key={s.operator} className="premium-card scraper-card">
                        <div className="scraper-main">
                            <div className={`status-dot ${isOnline ? 'online' : 'stale'}`}></div>
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
                    );
                })}
            </div>
            <style jsx>{`
                .admin-section { margin-bottom: 64px; }
                .section-title { margin-bottom: 24px; font-size: 1.4rem; font-weight: 700; color: var(--text-primary); }
                .scraper-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
                .scraper-card { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-radius: 20px; background: var(--surface-color); border: 1px solid var(--border-color); transition: 0.3s; box-shadow: var(--shadow-sm); }
                .scraper-card:hover { border-color: var(--accent-primary); box-shadow: 0 10px 25px -5px var(--accent-glow); transform: translateY(-4px); }
                .scraper-main { display: flex; align-items: center; gap: 16px; }
                .status-dot { width: 12px; height: 12px; border-radius: 50%; position: relative; }
                .status-dot.online { background: var(--status-success); box-shadow: 0 0 10px var(--status-success); }
                .status-dot.stale { background: var(--status-warning); box-shadow: 0 0 10px var(--status-warning); }
                .status-dot::after { content: ''; position: absolute; top: -4px; left: -4px; right: -4px; bottom: -4px; border-radius: 50%; background: currentColor; opacity: 0.2; animation: pulse 2s infinite; }
                @keyframes pulse { 0% { transform: scale(1); opacity: 0.3; } 70% { transform: scale(2); opacity: 0; } 100% { transform: scale(1); opacity: 0; } }
                .operator-name { font-weight: 800; font-size: 1.1rem; color: var(--text-primary); letter-spacing: 0.03em; }
                .last-scrape { font-size: 0.8rem; color: var(--text-muted); display: block; margin-top: 4px; font-weight: 500; }
                .scraper-date { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; background: var(--surface-hover); padding: 4px 10px; border-radius: 8px; }
            `}</style>
        </section>
    );
}

ScraperHealth.propTypes = {
    scrapers: PropTypes.array.isRequired,
    lang: PropTypes.string.isRequired,
};

/**
 * Component for Report Moderation Table
 */
function ReportModeration({ reports, handleReportAction, lang }) {
    return (
        <section className="admin-section">
            <h2 className="section-title font-heading">{lang === "sv" ? "Ärendehantering" : "User Report Moderation"}</h2>
            <div className="premium-card table-card">
                <div className="table-wrapper custom-scrollbar">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                                <th>{lang === "sv" ? "Ärende" : "Title"}</th>
                                <th>Status</th>
                                <th>{lang === "sv" ? "Datum" : "Date"}</th>
                                <th>{lang === "sv" ? "Åtgärd" : "Actions"}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reports.map((r) => (
                                <tr key={r.id} className="jsx-f02787c936080277">
                                    <td className="jsx-3261c0b2e58416a9 op-cell">{r.operator_name || "General"}</td>
                                    <td className="jsx-3261c0b2e58416a9 title-cell">{r.title}</td>
                                    <td>
                                        <span className={`jsx-f02787c936080277 status-badge-mini ${r.status}`}>
                                            {r.status}
                                        </span>
                                    </td>
                                    <td className="jsx-f02787c936080277 date-cell">
                                        {r.created_at ? new Date(r.created_at).toLocaleDateString() : "-"}
                                    </td>
                                    <td className="jsx-3261c0b2e58416a9 actions-cell">
                                        {r.status === "pending" ? (
                                            <div className="jsx-f02787c936080277 action-btns">
                                                <button onClick={() => handleReportAction(r.id, "verify")} className="jsx-f02787c936080277 btn-verify">Verify</button>
                                                <button onClick={() => handleReportAction(r.id, "reject")} className="jsx-f02787c936080277 btn-reject">Reject</button>
                                            </div>
                                        ) : (
                                            <span className="jsx-f02787c936080277 processed-label">Processed</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <style jsx>{`
                .admin-section { margin-bottom: 64px; }
                .section-title { margin-bottom: 24px; font-size: 1.4rem; font-weight: 700; color: var(--text-primary); }
                .table-card { padding: 0; overflow: hidden; box-shadow: var(--shadow-md); border-radius: 20px; border: 1px solid var(--border-color); background: var(--surface-color); }
                .table-wrapper { overflow-x: auto; max-height: 800px; }
                .admin-table { width: 100%; border-collapse: separate; border-spacing: 0; text-align: left; }
                .admin-table th { position: sticky; top: 0; z-index: 10; padding: 20px 24px; background: var(--surface-hover); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); font-weight: 800; border-bottom: 2px solid var(--border-color); }
                .admin-table td { padding: 20px 24px; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; vertical-align: middle; transition: 0.2s; }
                .admin-table tr:last-child td { border-bottom: none; }
                .admin-table tr:hover td { background: var(--surface-hover); }
                .op-cell { font-weight: 800; color: var(--accent-primary); text-transform: capitalize; }
                .title-cell { font-weight: 600; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-primary); }
                .status-badge-mini { padding: 6px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; border: 1px solid transparent; }
                .status-badge-mini.active { background: rgba(225, 29, 72, 0.1); color: var(--status-critical); border-color: rgba(225, 29, 72, 0.2); }
                .status-badge-mini.detecting { background: rgba(225, 29, 72, 0.1); color: var(--status-critical); border-color: rgba(225, 29, 72, 0.2); }
                .status-badge-mini.pending { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.investigating { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.identified { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.verified { background: rgba(5, 150, 105, 0.1); color: var(--status-success); border-color: rgba(5, 150, 105, 0.2); }
                .status-badge-mini.monitoring { background: rgba(5, 150, 105, 0.1); color: var(--status-success); border-color: rgba(5, 150, 105, 0.2); }
                .status-badge-mini.scheduled { background: rgba(79, 70, 229, 0.1); color: var(--accent-primary); border-color: rgba(79, 70, 229, 0.2); }
                .status-badge-mini.resolved { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border-color: var(--border-color); }
                .status-badge-mini.closed { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border-color: var(--border-color); }
                .action-btns { display: flex; gap: 8px; }
                .btn-verify, .btn-reject { padding: 8px 16px; border-radius: 10px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--border-color); background: var(--surface-color); cursor: pointer; transition: 0.2s; }
                .btn-verify { color: var(--status-success); }
                .btn-verify:hover { background: var(--status-success); color: white; border-color: var(--status-success); box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2); }
                .btn-reject { color: var(--status-critical); }
                .btn-reject:hover { background: var(--status-critical); color: white; border-color: var(--status-critical); box-shadow: 0 4px 12px rgba(225, 29, 72, 0.2); }
                .processed-label { font-size: 0.8rem; color: var(--text-muted); font-weight: 700; font-style: italic; }
            `}</style>
        </section>
    );
}

ReportModeration.propTypes = {
    reports: PropTypes.array.isRequired,
    handleReportAction: PropTypes.func.isRequired,
    lang: PropTypes.string.isRequired,
};

/**
 * Component for Outage Management Table
 */
const OutageRow = ({ o, lang, startEditing }) => {
    const rowClass = o.quality_issues?.length > 0 ? "row-low-quality" : "";
    const coordClass = o.latitude ? "" : "text-error";
    const fallbackText = lang === "sv" ? "Saknas" : "Missing";
    const coordText = o.latitude 
        ? `${o.latitude.toFixed(4)}, ${o.longitude.toFixed(4)}` 
        : fallbackText;

    return (
        <tr className={rowClass}>
            <td className="id-cell">
                #{o.id}
                {o.quality_issues?.includes("missing_coords") && <span className="quality-tag" title="Missing Coordinates">📍</span>}
                {o.quality_issues?.includes("missing_end_date") && <span className="quality-tag" title="Missing End Date">⏱️</span>}
            </td>
            <td className="op-cell">{o.operator_name}</td>
            <td className="title-cell">{o.title[lang] || o.title['sv']}</td>
            <td>
                <span className={`status-badge-mini ${o.status}`}>
                    {o.status}
                </span>
            </td>
            <td className={`coord-cell ${coordClass}`}>
                {coordText}
            </td>
            <td className="actions-cell">
                <button onClick={() => startEditing(o)} className="btn-edit">
                    {lang === "sv" ? "Redigera" : "Edit"}
                </button>
            </td>
        </tr>
    );
};

OutageRow.propTypes = {
    o: PropTypes.object.isRequired,
    lang: PropTypes.string.isRequired,
    startEditing: PropTypes.func.isRequired,
};

const OutageTableBody = ({ outagesLoading, outages, lang, startEditing }) => {
    if (outagesLoading) {
        return (
            <tr>
                <td colSpan="6" style={{ textAlign: "center", padding: "3rem" }}>
                    <div className="loading-spinner"></div>
                </td>
            </tr>
        );
    }
    
    if (outages.length === 0) {
        return (
            <tr>
                <td colSpan="6" style={{ textAlign: "center", padding: "3rem", opacity: 0.5 }}>
                    {lang === "sv" ? "Inga driftstörningar hittades" : "No outages found"}
                </td>
            </tr>
        );
    }

    return outages.map((o) => (
        <OutageRow key={o.id} o={o} lang={lang} startEditing={startEditing} />
    ));
};

OutageTableBody.propTypes = {
    outagesLoading: PropTypes.bool.isRequired,
    outages: PropTypes.array.isRequired,
    lang: PropTypes.string.isRequired,
    startEditing: PropTypes.func.isRequired,
};

const getTranslations = (lang) => ({
    heading: lang === "sv" ? "Hantera driftstörningar" : "Outage Management",
    searchPlaceholder: lang === "sv" ? "Sök (ID, Titel, Plats)..." : "Search (ID, Title, Location)...",
    allOps: lang === "sv" ? "Alla operatörer" : "All Operators",
    allStats: lang === "sv" ? "Alla statusar" : "All Statuses",
    active: lang === "sv" ? "Aktiv" : "Active",
    investigating: lang === "sv" ? "Undersöker" : "Investigating",
    scheduled: lang === "sv" ? "Planerad" : "Scheduled",
    resolved: lang === "sv" ? "Löst" : "Resolved",
    closed: lang === "sv" ? "Stängd" : "Closed",
    missingCoords: lang === "sv" ? "Saknar koordinater" : "Missing Coords",
    missingEndDate: lang === "sv" ? "Saknar slutdatum" : "Missing End Date",
    networkSharingTitle: lang === "sv" ? "Nätverksdelning (Operatörer under samma nät)" : "Network Sharing (MVNOs under the same network)",
    networkSharingDesc: lang === "sv" ? "Flera varumärken hyr in sig på och delar samma mobilmaster (Infrastruktur). En driftstörning hos huvudoperatören påverkar även dessa:" : "Several brands lease and share the same cell towers (Infrastructure). An outage at the main operator also affects these:",
    operator: lang === "sv" ? "Operatör" : "Operator",
    title: lang === "sv" ? "Titel" : "Title",
    coordinates: lang === "sv" ? "Position" : "Coordinates",
    actions: lang === "sv" ? "Åtgärd" : "Actions",
    prevPage: lang === "sv" ? "← Föregående" : "← Previous",
    nextPage: lang === "sv" ? "Nästa →" : "Next →",
    pageIndicator: (p) => lang === "sv" ? `Sida ${p + 1}` : `Page ${p + 1}`
});

function OutageManagement({ outageMgr, lang }) {
    const t = getTranslations(lang);

    const { 
        outages, outagesLoading, startEditing, page, hasMore, fetchOutages, 
        searchQuery, filterOperator, filterStatus, setPage, setSearchQuery,
        setFilterOperator, setFilterStatus, handleFilterChange, searchTimerRef,
        filterMissingCoords, setFilterMissingCoords, filterMissingEndDate, setFilterMissingEndDate
    } = outageMgr;
    
    const onSearchChange = (e) => {
        const val = e.target.value;
        setSearchQuery(val);
        clearTimeout(searchTimerRef.current);
        searchTimerRef.current = setTimeout(() => {
            handleFilterChange(val, filterOperator, filterStatus);
        }, 400);
    };

    const onOperatorChange = (e) => { 
        setFilterOperator(e.target.value); 
        handleFilterChange(searchQuery, e.target.value, filterStatus); 
    };

    const onStatusChange = (e) => { 
        setFilterStatus(e.target.value); 
        handleFilterChange(searchQuery, filterOperator, e.target.value); 
    };

    const onMissingCoordsChange = (e) => {
        setFilterMissingCoords(e.target.checked);
        handleFilterChange(searchQuery, filterOperator, filterStatus, e.target.checked, filterMissingEndDate);
    };

    const onMissingEndDateChange = (e) => {
        setFilterMissingEndDate(e.target.checked);
        handleFilterChange(searchQuery, filterOperator, filterStatus, filterMissingCoords, e.target.checked);
    };

    const handlePrevPage = () => {
        const newPage = page - 1;
        setPage(newPage);
        fetchOutages(newPage);
    };

    const handleNextPage = () => {
        const newPage = page + 1;
        setPage(newPage);
        fetchOutages(newPage);
    };

    return (
        <section className="admin-section">
            <div className="section-header-row">
                <h2 className="section-title font-heading" style={{ marginBottom: 0 }}>{t.heading}</h2>

                <div className="filter-controls">
                    <div className="filter-group">
                        <input
                            type="text"
                            placeholder={t.searchPlaceholder}
                            value={searchQuery}
                            onChange={onSearchChange}
                            className="search-input"
                        />
                    </div>
                    <div className="filter-group">
                        <select
                            value={filterOperator}
                            onChange={onOperatorChange}
                            className="filter-select"
                        >
                            <option value="">{t.allOps}</option>
                            <option value="telia">Telia</option>
                            <option value="telenor">Telenor</option>
                            <option value="tre">Tre</option>
                        </select>
                        <select
                            value={filterStatus}
                            onChange={onStatusChange}
                            className="filter-select"
                        >
                            <option value="">{t.allStats}</option>
                            <option value="active">{t.active}</option>
                            <option value="investigating">{t.investigating}</option>
                            <option value="scheduled">{t.scheduled}</option>
                            <option value="resolved">{t.resolved}</option>
                            <option value="closed">{t.closed}</option>
                        </select>
                    </div>
                    <div className="quality-filters">
                        <label className="filter-checkbox">
                            <input 
                                type="checkbox" 
                                checked={filterMissingCoords} 
                                onChange={onMissingCoordsChange} 
                            />
                            <span>{t.missingCoords}</span>
                        </label>
                        <label className="filter-checkbox">
                            <input 
                                type="checkbox" 
                                checked={filterMissingEndDate} 
                                onChange={onMissingEndDateChange} 
                            />
                            <span>{t.missingEndDate}</span>
                        </label>
                    </div>
                </div>
            </div>

            <div className="network-sharing-note">
                <h4 className="sharing-title">
                    <span className="icon">ℹ️</span> 
                    {t.networkSharingTitle}
                </h4>
                <p className="sharing-text">
                    {t.networkSharingDesc}
                </p>
                <ul className="sharing-list">
                    <li><strong>Telia:</strong> Halebop, Fello</li>
                    <li><strong>Tele2:</strong> Comviq (shares network with Telenor)</li>
                    <li><strong>Telenor:</strong> Lycamobile, Vimla, Fibio</li>
                    <li><strong>Tre:</strong> Hallon</li>
                </ul>
            </div>

            <div className="premium-card table-card">
                <div className="table-wrapper custom-scrollbar">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>{t.operator}</th>
                                <th>{t.title}</th>
                                <th>Status</th>
                                <th>{t.coordinates}</th>
                                <th>{t.actions}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <OutageTableBody outagesLoading={outagesLoading} outages={outages} lang={lang} startEditing={startEditing} />
                        </tbody>
                    </table>
                </div>

                <div className="pagination-controls">
                    <button
                        className="btn-secondary"
                        disabled={page === 0 || outagesLoading}
                        onClick={handlePrevPage}
                    >
                        {t.prevPage}
                    </button>
                    <span className="page-indicator">
                        {t.pageIndicator(page)}
                    </span>
                    <button
                        className="btn-secondary"
                        disabled={!hasMore || outagesLoading}
                        onClick={handleNextPage}
                    >
                        {t.nextPage}
                    </button>
                </div>
            </div>
            <style jsx global>{`
                .admin-section { margin-bottom: 64px; }
                .section-header-row { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 24px; margin-bottom: 32px; }
                .section-title { margin-bottom: 24px; font-size: 1.4rem; font-weight: 700; color: var(--text-primary); }
                .filter-controls { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; background: var(--surface-color); padding: 12px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: var(--shadow-sm); }
                .filter-group { display: flex; gap: 8px; align-items: center; }
                .search-input { padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-primary); font-size: 0.9rem; min-width: 280px; transition: border-color 0.2s; }
                .search-input:focus { border-color: var(--accent-primary); outline: none; }
                .filter-select { padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-primary); font-size: 0.9rem; cursor: pointer; transition: border-color 0.2s; }
                .filter-select:hover { border-color: var(--accent-primary); }
                .quality-filters { display: flex; gap: 20px; align-items: center; padding: 0 12px; border-left: 1px solid var(--border-color); }
                .filter-checkbox { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; user-select: none; transition: color 0.2s; }
                .filter-checkbox:hover { color: var(--text-primary); }
                .filter-checkbox input { width: 16px; height: 16px; cursor: pointer; accent-color: var(--accent-primary); }
                .network-sharing-note { margin: 24px 0; padding: 24px; background: var(--accent-glow); border-left: 5px solid var(--accent-primary); border-radius: 0 12px 12px 0; }
                .sharing-title { margin: 0 0 12px 0; display: flex; align-items: center; gap: 10px; color: var(--text-primary); font-size: 1.1rem; }
                .sharing-text { margin: 0 0 16px 0; font-size: 0.95rem; color: var(--text-secondary); opacity: 0.9; }
                .sharing-list { margin: 0; padding-left: 20px; font-size: 0.9rem; color: var(--text-primary); display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
                .table-card { padding: 0; overflow: hidden; box-shadow: var(--shadow-md); border-radius: 20px; border: 1px solid var(--border-color); background: var(--surface-color); }
                .table-wrapper { overflow-x: auto; max-height: 800px; }
                .admin-table { width: 100%; border-collapse: separate; border-spacing: 0; text-align: left; }
                .admin-table th { position: sticky; top: 0; z-index: 10; padding: 20px 24px; background: var(--surface-hover); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); font-weight: 800; border-bottom: 2px solid var(--border-color); }
                .admin-table td { padding: 20px 24px; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; vertical-align: middle; transition: 0.2s; }
                .admin-table tr:last-child td { border-bottom: none; }
                .admin-table tr:hover td { background: var(--surface-hover); }
                .row-low-quality { background: rgba(225, 29, 72, 0.03); }
                .row-low-quality:hover td { background: rgba(225, 29, 72, 0.08) !important; }
                .quality-tag { margin-left: 8px; font-size: 1.1rem; vertical-align: middle; cursor: help; }
                .text-error { color: var(--status-critical); font-weight: 800; }

                .op-cell { font-weight: 800; color: var(--accent-primary); text-transform: capitalize; }
                .id-cell { font-family: 'JetBrains Mono', monospace; color: var(--text-muted); font-size: 0.8rem; font-weight: 600; }
                .title-cell { font-weight: 600; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-primary); }
                .status-badge-mini { padding: 6px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; border: 1px solid transparent; }
                .status-badge-mini.active { background: rgba(225, 29, 72, 0.1); color: var(--status-critical); border-color: rgba(225, 29, 72, 0.2); }
                .status-badge-mini.detecting { background: rgba(225, 29, 72, 0.1); color: var(--status-critical); border-color: rgba(225, 29, 72, 0.2); }
                .status-badge-mini.pending { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.investigating { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.identified { background: rgba(217, 119, 6, 0.1); color: var(--status-warning); border-color: rgba(217, 119, 6, 0.2); }
                .status-badge-mini.verified { background: rgba(5, 150, 105, 0.1); color: var(--status-success); border-color: rgba(5, 150, 105, 0.2); }
                .status-badge-mini.monitoring { background: rgba(5, 150, 105, 0.1); color: var(--status-success); border-color: rgba(5, 150, 105, 0.2); }
                .status-badge-mini.scheduled { background: rgba(79, 70, 229, 0.1); color: var(--accent-primary); border-color: rgba(79, 70, 229, 0.2); }
                .status-badge-mini.resolved { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border-color: var(--border-color); }
                .status-badge-mini.closed { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border-color: var(--border-color); }
                .btn-edit { padding: 8px 16px; border-radius: 10px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--border-color); background: var(--surface-color); cursor: pointer; transition: 0.2s; color: var(--accent-primary); }
                .btn-edit:hover { background: var(--accent-primary); color: white; border-color: var(--accent-primary); box-shadow: 0 4px 12px var(--accent-glow); }
                .pagination-controls { display: flex; justify-content: space-between; align-items: center; padding: 24px; background: var(--surface-hover); border-top: 1px solid var(--border-color); }
                .btn-secondary { padding: 10px 20px; border-radius: 10px; font-weight: 700; background: var(--surface-color); border: 1px solid var(--border-color); color: var(--text-primary); cursor: pointer; font-size: 0.85rem; }
                .btn-secondary:hover:not(:disabled) { border-color: var(--accent-primary); color: var(--accent-primary); }
                .btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
                .page-indicator { font-weight: 800; font-size: 0.95rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
                .loading-spinner { width: 48px; height: 48px; border: 4px solid var(--accent-glow); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
                @keyframes spin { to { transform: rotate(360deg); } }
                @media (max-width: 1024px) { .filter-controls { flex-direction: column; align-items: stretch; } .quality-filters { border-left: none; border-top: 1px solid var(--border-color); padding: 12px 0 0 0; } }
            `}</style>
        </section>
    );
}

OutageManagement.propTypes = {
    outageMgr: PropTypes.object.isRequired,
    lang: PropTypes.string.isRequired,
};

/**
 * Main Admin Page Component
 */
export default function AdminPage() {
    const { lang } = useLanguage();
    const [mounted, setMounted] = useState(false);
    
    const adminData = useAdminData();
    const outageMgr = useOutageManagement();
    
    const { fetchData } = adminData;
    const { fetchOutages } = outageMgr;

    useEffect(() => {
        setMounted(true);
        fetchData();
        fetchOutages(0);
    }, [fetchData, fetchOutages]);

    useEffect(() => {
        if (outageMgr.editingOutage) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => { document.body.style.overflow = 'unset'; };
    }, [outageMgr.editingOutage]);

    if (!mounted || adminData.loading) return <div className="loading">Loading...</div>;

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

            <ScraperHealth scrapers={adminData.scrapers} lang={lang} />
            
            <ReportModeration 
                reports={adminData.reports} 
                handleReportAction={adminData.handleReportAction} 
                lang={lang} 
            />

            <OutageManagement outageMgr={outageMgr} lang={lang} />

            {outageMgr.editingOutage && createPortal(
                <div className="modal-overlay">
                    <div className="premium-card modal-content animate-slide-up">
                        <header className="modal-header">
                            <h3>{lang === "sv" ? "Redigera driftstörning" : "Edit Outage"} #{outageMgr.editingOutage.id}</h3>
                            <button className="close-btn" onClick={() => outageMgr.setEditingOutage(null)}>×</button>
                        </header>
                        <form onSubmit={outageMgr.handleUpdateOutage} className="edit-form">
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="incident_id">Incident ID</label>
                                    <input id="incident_id" value={outageMgr.editForm.incident_id} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, incident_id: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="operator_id">Operator ID</label>
                                    <input id="operator_id" type="number" value={outageMgr.editForm.operator_id} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, operator_id: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="region_id">Region ID</label>
                                    <input id="region_id" type="number" value={outageMgr.editForm.region_id} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, region_id: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="raw_data_id">Raw Data ID</label>
                                    <input id="raw_data_id" type="number" value={outageMgr.editForm.raw_data_id} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, raw_data_id: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="title_sv">Title (Svenska)</label>
                                    <input id="title_sv" value={outageMgr.editForm.title_sv} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, title_sv: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="title_en">Title (English)</label>
                                    <input id="title_en" value={outageMgr.editForm.title_en} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, title_en: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="description_sv">Description (Svenska)</label>
                                <textarea id="description_sv" value={outageMgr.editForm.description_sv} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, description_sv: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label htmlFor="description_en">Description (English)</label>
                                <textarea id="description_en" value={outageMgr.editForm.description_en} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, description_en: e.target.value })} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="status">Status</label>
                                    <select id="status" value={outageMgr.editForm.status} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, status: e.target.value })}>
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
                                    <label htmlFor="severity">Severity</label>
                                    <select id="severity" value={outageMgr.editForm.severity} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, severity: e.target.value })}>
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
                                    <label htmlFor="start_time">Start Time</label>
                                    <input id="start_time" type="datetime-local" value={outageMgr.editForm.start_time} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, start_time: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="end_time">End Time</label>
                                    <input id="end_time" type="datetime-local" value={outageMgr.editForm.end_time} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, end_time: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="estimated_fix_time">Estimated Fix Time</label>
                                <input id="estimated_fix_time" type="datetime-local" value={outageMgr.editForm.estimated_fix_time} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, estimated_fix_time: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label htmlFor="place">Place (Plus Code or Address)</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <input
                                        id="place"
                                        style={{ flex: 1 }}
                                        placeholder="Ex: M2GM+R6 Göteborg"
                                        value={outageMgr.editForm.place}
                                        onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, place: e.target.value })}
                                    />
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        style={{ padding: '8px 12px', whiteSpace: 'nowrap' }}
                                        onClick={outageMgr.handleResolvePlace}
                                    >
                                        {lang === "sv" ? "Hämta info" : "Resolve"}
                                    </button>
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="location">Location Name</label>
                                <input id="location" value={outageMgr.editForm.location} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, location: e.target.value })} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="latitude">Latitude</label>
                                    <input id="latitude" type="number" step="any" value={outageMgr.editForm.latitude} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, latitude: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="longitude">Longitude</label>
                                    <input id="longitude" type="number" step="any" value={outageMgr.editForm.longitude} onChange={e => outageMgr.setEditForm({ ...outageMgr.editForm, longitude: e.target.value })} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>{lang === "sv" ? "Påverkade Tjänster" : "Affected Services"}</label>
                                <div className="checkbox-group">
                                    {["5g+", "5g", "4g", "3g", "2g"].map(service => (
                                        <label key={service} className="checkbox-label">
                                            <input
                                                type="checkbox"
                                                checked={outageMgr.editForm.affected_services.includes(service)}
                                                onChange={(e) => {
                                                    const current = new Set(outageMgr.editForm.affected_services);
                                                    if (e.target.checked) current.add(service);
                                                    else current.delete(service);
                                                    outageMgr.setEditForm({ ...outageMgr.editForm, affected_services: Array.from(current) });
                                                }}
                                            />
                                            {service}
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <footer className="modal-footer">
                                <button type="button" className="btn-secondary" onClick={() => outageMgr.setEditingOutage(null)}>Cancel</button>
                                <button type="submit" className="btn-primary">Save Changes</button>
                            </footer>
                        </form>
                    </div>
                </div>,
                document.body
            )}

            <style jsx>{`
                .admin-container { padding: 40px; max-width: 1400px; margin: 0 auto; }
                .admin-header { margin-bottom: 48px; padding-bottom: 32px; border-bottom: 1px solid var(--border-color); }
                .admin-header h1 { font-size: 2.4rem; margin-bottom: 8px; }
                .subtitle { color: var(--text-muted); font-size: 1rem; }
                
                /* Modal & Forms (Globally applied since modal is portaled) */
                :global(.modal-overlay) { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 20px; }
                :global(.modal-content) { width: 100%; max-width: 700px; max-height: 90vh; overflow-y: auto; background: var(--surface-color); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg); }
                :global(.modal-header) { display: flex; justify-content: space-between; align-items: center; padding: 24px 32px; border-bottom: 1px solid var(--border-color); }
                :global(.modal-header h3) { font-size: 1.25rem; }
                :global(.close-btn) { font-size: 2rem; color: var(--text-muted); line-height: 1; }
                :global(.close-btn:hover) { color: var(--text-primary); }
                :global(.edit-form) { padding: 32px; }
                :global(.form-group) { margin-bottom: 24px; }
                :global(.form-group label) { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
                :global(.form-group input), :global(.form-group textarea), :global(.form-group select) { width: 100%; padding: 12px 16px; border-radius: 8px; background: var(--bg-color); border: 1px solid var(--border-color); color: var(--text-primary); font-size: 1rem; transition: border-color 0.2s; }
                :global(.form-group input:focus), :global(.form-group textarea:focus) { border-color: var(--accent-primary); outline: none; }
                :global(.form-row) { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                :global(.modal-footer) { margin-top: 40px; display: flex; justify-content: flex-end; gap: 16px; padding-top: 24px; border-top: 1px solid var(--border-color); }
                :global(.btn-primary) { background: var(--accent-primary); color: white; border: none; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; box-shadow: 0 4px 12px var(--accent-glow); }
                :global(.btn-primary:hover) { background: var(--accent-secondary); transform: translateY(-1px); }
                :global(.checkbox-group) { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 12px; }
                :global(.checkbox-label) { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; cursor: pointer; color: var(--text-primary); }
                :global(.checkbox-label input) { width: auto; margin: 0; }
                
                .loading { display: flex; align-items: center; justify-content: center; min-height: 80vh; font-size: 1.2rem; font-weight: 600; color: var(--accent-primary); }
                @media (max-width: 1024px) { .admin-container { padding: 24px; } }
            `}</style>
        </div>
    );
}
