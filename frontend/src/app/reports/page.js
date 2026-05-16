"use client";

import { useEffect, useState, Suspense, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import PropTypes from "prop-types";

/**
 * Helper to determine display status
 */
const getEffectiveStatus = (outageObj) => {
    if (outageObj?.status?.toLowerCase() === 'resolved') return 'resolved';
    
    const endDateStr = outageObj?.end_time || outageObj?.estimated_fix_time;
    if (endDateStr) {
        const endDate = new Date(endDateStr);
        if (!Number.isNaN(endDate.getTime()) && endDate < new Date()) {
            return 'resolved';
        }
    }
    return outageObj?.status || 'active';
};

/**
 * Filter predicate for search
 */
const matchesSearchQuery = (outage, searchTerm, t) => {
    if (!searchTerm) return true;
    const lowerSearch = searchTerm.toLowerCase();
    const title = t(outage.title).toLowerCase();
    const operator = outage.operator_name.toLowerCase();
    const location = (outage.location || "").toLowerCase();
    
    return title.includes(lowerSearch) ||
           operator.includes(lowerSearch) ||
           location.includes(lowerSearch);
};

/**
 * Filter predicate for operator
 */
const matchesOperatorFilter = (outage, operatorFilter) => {
    return operatorFilter === "all" || 
           outage.operator_name.toLowerCase() === operatorFilter.toLowerCase();
};

/**
 * Filter predicate for service
 */
const matchesServiceFilter = (outage, serviceFilter) => {
    if (serviceFilter === "all") return true;
    const services = new Set((outage.affected_services || []).map(s => s.toLowerCase()));
    return services.has(serviceFilter.toLowerCase());
};

/**
 * Filter predicate for status
 */
const matchesStatusFilter = (outage, statusFilter) => {
    if (statusFilter === "all") return true;
    const displayStatus = getEffectiveStatus(outage);
    return statusFilter.toLowerCase() === displayStatus.toLowerCase();
};

/**
 * Formats date string to YYYY/MM/DD
 */
const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return "-";

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');

    return `${year}/${month}/${day}`;
};

/**
 * Sub-component for filter controls
 */
const FilterControls = ({ lang, operators, operatorFilter, setOperatorFilter, statusFilter, setStatusFilter, serviceFilter, setServiceFilter, search, setSearch }) => (
    <div className="filters-container">
        <div className="filter-group">
            <select
                value={operatorFilter}
                onChange={(e) => setOperatorFilter(e.target.value)}
                className="service-select"
            >
                <option value="all">{lang === "sv" ? "Alla Operatörer" : "All Operators"}</option>
                {operators.map(op => (
                    <option key={op.id} value={op.name.toLowerCase()}>{op.name.charAt(0).toUpperCase() + op.name.slice(1)}</option>
                ))}
            </select>
            <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="service-select"
            >
                <option value="all">{lang === "sv" ? "Alla Status" : "All Status"}</option>
                <option value="active">{lang === "sv" ? "Aktiva" : "Active"}</option>
                <option value="investigating">{lang === "sv" ? "Undersöker" : "Investigating"}</option>
                <option value="scheduled">{lang === "sv" ? "Planerat" : "Scheduled"}</option>
                <option value="resolved">{lang === "sv" ? "Lösta" : "Resolved"}</option>
            </select>
            <select
                value={serviceFilter}
                onChange={(e) => setServiceFilter(e.target.value)}
                className="service-select"
            >
                <option value="all">{lang === "sv" ? "Alla Tjänster" : "All Services"}</option>
                {["5g+", "5g", "4g", "3g", "2g"].map(s => (
                    <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
            </select>
        </div>
        <div className="search-bar">
            <input
                type="text"
                placeholder={lang === "sv" ? "Sök på operatör, plats..." : "Search operator, location..."}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
            />
        </div>
        <style jsx>{`
            .filters-container { display: flex; gap: 12px; align-items: center; }
            .filter-group { display: flex; gap: 8px; }
            .service-select { padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--surface-color); color: var(--text-primary); font-size: 0.9rem; cursor: pointer; transition: var(--transition-base); }
            .service-select:focus { outline: none; border-color: var(--accent-primary); box-shadow: 0 0 0 3px var(--accent-glow); }
            .search-bar input { padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--surface-color); width: 300px; font-size: 0.9rem; transition: var(--transition-base); }
            .search-bar input:focus { outline: none; border-color: var(--accent-primary); box-shadow: 0 0 0 3px var(--accent-glow); }
            @media (max-width: 768px) {
                .filters-container { flex-direction: column; align-items: stretch; }
                .filter-group { flex-direction: column; }
                .search-bar input { width: 100%; }
            }
        `}</style>
    </div>
);

FilterControls.propTypes = {
    lang: PropTypes.string.isRequired,
    operators: PropTypes.array.isRequired,
    operatorFilter: PropTypes.string.isRequired,
    setOperatorFilter: PropTypes.func.isRequired,
    statusFilter: PropTypes.string.isRequired,
    setStatusFilter: PropTypes.func.isRequired,
    serviceFilter: PropTypes.string.isRequired,
    setServiceFilter: PropTypes.func.isRequired,
    search: PropTypes.string.isRequired,
    setSearch: PropTypes.func.isRequired,
};

/**
 * Sub-component for report row
 */
const ReportRow = ({ outage, lang, t }) => {
    const displayStatus = getEffectiveStatus(outage);
    const fallbackLoc = lang === "sv" ? "Sverige" : "Sweden";
    const locationDisplay = outage.region_name ? t(outage.region_name) : fallbackLoc;
    
    const priority = ["5g+", "5g", "4g", "3g", "2g", "voice", "data", "sms", "mms", "fiber", "broadband"];
    const sortedServices = [...(outage.affected_services || [])].sort((a, b) => {
        const idxA = priority.indexOf(a.toLowerCase());
        const idxB = priority.indexOf(b.toLowerCase());
        return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
    });

    return (
        <tr>
            <td>
                <span className={`status-badge-mini ${displayStatus.toLowerCase()}`}>
                    {displayStatus}
                </span>
            </td>
            <td className="operator-cell">{outage.operator_name}</td>
            <td className="title-cell">
                {outage.incident_id || t(outage.title) || "-"}
            </td>
            <td className="services-cell">
                <div className="service-tags-mini">
                    {sortedServices.slice(0, 5).map((s) => (
                        <span key={s} className={`mini-tag ${["5g+", "5g", "4g", "3g", "2g"].includes(s.toLowerCase()) ? 'mobile' : ''}`}>{s}</span>
                    ))}
                    {sortedServices.length > 5 && (
                        <span className="mini-tag more">+{sortedServices.length - 5}</span>
                    )}
                </div>
            </td>
            <td className="location-cell">
                {locationDisplay}
            </td>
            <td className="date-cell">
                {formatDate(outage.start_time)}
            </td>
            <td className="date-cell">
                {formatDate(outage.end_time || outage.estimated_fix_time)}
            </td>
            <td className="actions-cell">
                <Link href={`/outage?id=${outage.id}`} className="view-link">
                    {lang === "sv" ? "Visa" : "View"}
                </Link>
            </td>
            <style jsx>{`
                td { padding: 14px 20px; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; }
                .operator-cell { font-weight: 700; color: var(--accent-primary); }
                .title-cell { font-weight: 500; }
                .location-cell { color: var(--text-secondary); }
                .service-tags-mini { display: flex; gap: 4px; flex-wrap: wrap; }
                .mini-tag { font-size: 0.65rem; background: var(--surface-hover); padding: 2px 6px; border-radius: 4px; color: var(--text-secondary); border: 1px solid var(--border-color); }
                .status-badge-mini { padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; display: inline-block; }
                .status-badge-mini.active { color: var(--status-critical); border: 1px solid var(--status-critical); }
                .status-badge-mini.resolved { color: var(--status-success); border: 1px solid var(--status-success); }
                .status-badge-mini.investigating { color: var(--status-warning); border: 1px solid var(--status-warning); }
                .status-badge-mini.scheduled { color: var(--accent-primary); border: 1px solid var(--accent-primary); }
                .mini-tag.mobile { background: rgba(0, 243, 255, 0.1); color: #00f3ff; border-color: #00f3ff; }
                .view-link { color: var(--accent-primary); text-decoration: none; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
                .view-link:hover { text-decoration: underline; }
                @media (max-width: 768px) {
                    td:nth-child(4) { display: none; }
                }
            `}</style>
        </tr>
    );
};

ReportRow.propTypes = {
    outage: PropTypes.object.isRequired,
    lang: PropTypes.string.isRequired,
    t: PropTypes.func.isRequired,
};

function ReportsContent() {
    const { lang, t } = useLanguage();
    const [outages, setOutages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [serviceFilter, setServiceFilter] = useState("all");
    const searchParams = useSearchParams();
    const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "all");
    const [operatorFilter, setOperatorFilter] = useState("all");
    const [operators, setOperators] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [ops, data] = await Promise.all([
                    api.operators.list(),
                    api.outages.list()
                ]);
                setOperators(ops);
                setOutages(data);
            } catch (err) {
                console.error("Failed to fetch reports data:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredOutages = useMemo(() => {
        return outages
            .filter(o => {
                return matchesSearchQuery(o, search, t) &&
                       matchesOperatorFilter(o, operatorFilter) &&
                       matchesServiceFilter(o, serviceFilter) &&
                       matchesStatusFilter(o, statusFilter);
            })
            .sort((a, b) => {
                const dateA = a.start_time ? new Date(a.start_time).getTime() : 0;
                const dateB = b.start_time ? new Date(b.start_time).getTime() : 0;
                return dateB - dateA;
            });
    }, [outages, search, operatorFilter, serviceFilter, statusFilter, t]);

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;

    return (
        <div className="reports-container animate-fade-in">
            <header className="page-header">
                <div className="header-content">
                    <h1 className="text-gradient">
                        {lang === "sv" ? "Alla Avbrott" : "All Incidents"}
                    </h1>
                    <p className="subtitle">
                        {lang === "sv" ? "Komplett lista över nätverksstörningar" : "Comprehensive database of network disruptions"}
                    </p>
                </div>
                <FilterControls 
                    lang={lang}
                    operators={operators}
                    operatorFilter={operatorFilter}
                    setOperatorFilter={setOperatorFilter}
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    serviceFilter={serviceFilter}
                    setServiceFilter={setServiceFilter}
                    search={search}
                    setSearch={setSearch}
                />
            </header>

            <div className="premium-card table-wrapper">
                <table className="outage-table">
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                            <th>{lang === "sv" ? "Händelse" : "Incident"}</th>
                            <th>{lang === "sv" ? "Tjänster" : "Services"}</th>
                            <th>{lang === "sv" ? "Plats" : "Location"}</th>
                            <th>{lang === "sv" ? "Startdatum" : "Start date"}</th>
                            <th>{lang === "sv" ? "Slutdatum" : "End date"}</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredOutages.map((outage) => (
                            <ReportRow key={outage.id} outage={outage} lang={lang} t={t} />
                        ))}
                    </tbody>
                </table>
                {filteredOutages.length === 0 && (
                    <div className="empty-state">
                        {lang === "sv" ? "Inga matchande avbrott hittades." : "No matching incidents found."}
                    </div>
                )}
            </div>

            <style jsx>{`
                .reports-container { padding: 40px; max-width: 1300px; margin: 0 auto; }
                .page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px; gap: 24px; flex-wrap: wrap; padding-bottom: 32px; border-bottom: 1px solid var(--border-color); }
                .header-content h1 { font-size: 2.2rem; margin-bottom: 8px; }
                .subtitle { color: var(--text-muted); font-size: 1rem; }
                .table-wrapper { padding: 0; overflow: hidden; border-radius: 20px; border: 1px solid var(--border-color); box-shadow: var(--shadow-md); background: var(--surface-color); }
                .outage-table { width: 100%; border-collapse: separate; border-spacing: 0; text-align: left; }
                .outage-table th { padding: 18px 24px; background: var(--surface-hover); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); font-weight: 800; border-bottom: 2px solid var(--border-color); }
                .empty-state { padding: 60px; text-align: center; color: var(--text-muted); font-weight: 600; font-size: 1.1rem; }
                .loading-container { height: 70vh; display: flex; align-items: center; justify-content: center; }
                .spinner { width: 48px; height: 48px; border: 4px solid var(--accent-glow); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 1s linear infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
                @media (max-width: 1024px) { .page-header { flex-direction: column; align-items: flex-start; } .outage-table th:nth-child(4) { display: none; } }
            `}</style>
        </div>
    );
}

export default function ReportsPage() {
    return (
        <Suspense fallback={<div className="loading-container"><div className="spinner"></div></div>}>
            <ReportsContent />
        </Suspense>
    );
}
