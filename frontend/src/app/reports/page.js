"use client";

import { useEffect, useState, Suspense } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

function ReportsContent() {
    const { lang, t } = useLanguage();
    const [outages, setOutages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [serviceFilter, setServiceFilter] = useState("all");
    const searchParams = useSearchParams();
    const initialStatus = searchParams.get("status") || "all";
    const [statusFilter, setStatusFilter] = useState(initialStatus);
    const [operatorFilter, setOperatorFilter] = useState("all");
    const [operators, setOperators] = useState([]);

    useEffect(() => {
        const fetchMetadata = async () => {
            try {
                const ops = await api.operators.list();
                setOperators(ops);
            } catch (err) {
                console.error("Failed to fetch operators:", err);
            }
        };
        fetchMetadata();
    }, []);

    useEffect(() => {
        const fetchOutages = async () => {
            try {
                const data = await api.outages.list();
                setOutages(data);
            } catch (err) {
                console.error("Failed to fetch outages:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchOutages();
    }, []);

    const filteredOutages = outages.filter(o => {
        const title = t(o.title).toLowerCase();
        const operator = o.operator_name.toLowerCase();
        const location = (o.location || "").toLowerCase();
        const searchTerm = search.toLowerCase();

        const matchesSearch = title.includes(searchTerm) ||
            operator.includes(searchTerm) ||
            location.includes(searchTerm);

        if (!matchesSearch) return false;

        // Operator Filter
        if (operatorFilter !== "all" && o.operator_name.toLowerCase() !== operatorFilter.toLowerCase()) {
            return false;
        }

        // Service Filter
        if (serviceFilter !== "all") {
            const services = o.affected_services || [];
            const lowerServices = services.map(s => s.toLowerCase());

            let matchesService = false;
            // Precise matching for enum values
            if (serviceFilter === "5g+") matchesService = lowerServices.includes("5g+");
            else if (serviceFilter === "5g") matchesService = lowerServices.includes("5g");
            else if (serviceFilter === "4g") matchesService = lowerServices.includes("4g");
            else if (serviceFilter === "3g") matchesService = lowerServices.includes("3g");
            else if (serviceFilter === "2g") matchesService = lowerServices.includes("2g");
            else if (serviceFilter === "data") matchesService = lowerServices.includes("data");
            else if (serviceFilter === "voice") matchesService = lowerServices.includes("voice");
            else if (serviceFilter === "sms") matchesService = lowerServices.includes("sms");
            else if (serviceFilter === "mms") matchesService = lowerServices.includes("mms");
            else if (serviceFilter === "fiber") matchesService = lowerServices.includes("fiber");
            else if (serviceFilter === "broadband") matchesService = lowerServices.includes("broadband");
            else if (serviceFilter === "mobile") matchesService = lowerServices.includes("mobile");

            if (!matchesService) return false;
        }

        // Status Filter
        if (statusFilter !== "all") {
            if (statusFilter.toLowerCase() !== o.status.toLowerCase()) return false;
        }

        return true;
    }).sort((a, b) => {
        const dateA = a.start_time ? new Date(a.start_time) : new Date(0);
        const dateB = b.start_time ? new Date(b.start_time) : new Date(0);
        return dateB - dateA;
    });

    const formatDate = (dateStr) => {
        if (!dateStr) return "-";
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return "-";

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');

        return `${year}/${month}/${day}`;
    };

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
                            <option value="mobile">{lang === "sv" ? "Mobil" : "Mobile"}</option>
                            <option value="5g+">5G+</option>
                            <option value="5g">5G</option>
                            <option value="4g">4G</option>
                            <option value="3g">3G</option>
                            <option value="2g">2G</option>
                            <option value="data">{lang === "sv" ? "Mobildata" : "Mobile Data"}</option>
                            <option value="voice">{lang === "sv" ? "Röstsamtal" : "Voice Calls"}</option>
                            <option value="sms">SMS</option>
                            <option value="mms">MMS</option>
                            <option value="fiber">{lang === "sv" ? "Fiber" : "Fiber"}</option>
                            <option value="broadband">{lang === "sv" ? "Bredband" : "Broadband"}</option>
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
                </div>
            </header>

            <div className="premium-card table-wrapper">
                <table className="outage-table">
                    <thead>
                        <tr>
                            <th>{lang === "sv" ? "Status" : "Status"}</th>
                            <th>{lang === "sv" ? "Operatör" : "Operator"}</th>
                            <th>{lang === "sv" ? "Händelse" : "Incident"}</th>
                            <th>{lang === "sv" ? "Tjänster" : "Services"}</th>
                            <th>{lang === "sv" ? "Plats" : "Location"}</th>
                            <th>{lang === "sv" ? "Datum" : "Date"}</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredOutages.map((outage) => (
                            <tr key={outage.id}>
                                <td>
                                    <span className={`status-badge-mini ${outage.status.toLowerCase()}`}>
                                        {outage.status}
                                    </span>
                                </td>
                                <td className="operator-cell">{outage.operator_name}</td>
                                <td className="title-cell">
                                    {outage.incident_id
                                        ? `Incident ${outage.incident_id}`
                                        : (t(outage.title) || "-")}
                                </td>
                                <td className="services-cell">
                                    <div className="service-tags-mini">
                                        {(() => {
                                            const priority = ["5g+", "5g", "4g", "3g", "2g", "voice", "data", "sms", "mms", "fiber", "broadband"];
                                            const sorted = [...(outage.affected_services || [])].sort((a, b) => {
                                                const idxA = priority.indexOf(a.toLowerCase());
                                                const idxB = priority.indexOf(b.toLowerCase());
                                                return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
                                            });
                                            const displayLimit = 5;
                                            return (
                                                <>
                                                    {sorted.slice(0, displayLimit).map((s, i) => (
                                                        <span key={i} className={`mini-tag ${["5g+", "5g", "4g", "3g", "2g"].includes(s.toLowerCase()) ? 'mobile' : ''}`}>{s}</span>
                                                    ))}
                                                    {sorted.length > displayLimit && (
                                                        <span className="mini-tag more">+{sorted.length - displayLimit}</span>
                                                    )}
                                                </>
                                            );
                                        })()}
                                    </div>
                                </td>
                                <td className="location-cell">{outage.location || "Sweden"}</td>
                                <td className="date-cell">
                                    {formatDate(outage.start_time)}
                                </td>
                                <td className="actions-cell">
                                    <Link href={`/outages/${outage.id}`} className="view-link">
                                        {lang === "sv" ? "Visa" : "View"}
                                    </Link>
                                </td>
                            </tr>
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
                .reports-container {
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
                .header-content h1 { font-size: 1.8rem; margin-bottom: 4px; }
                .subtitle { color: var(--text-muted); font-size: 0.95rem; }
                
                .filters-container {
                    display: flex;
                    gap: 12px;
                    align-items: center;
                }
                
                .service-select {
                    padding: 10px 16px;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    background: var(--surface-color);
                    color: var(--text-primary);
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: var(--transition-base);
                }
                .service-select:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                    box-shadow: 0 0 0 3px var(--accent-glow);
                }

                .search-bar input {
                    padding: 10px 16px;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    background: var(--surface-color);
                    width: 300px;
                    font-size: 0.9rem;
                    transition: var(--transition-base);
                }
                .search-bar input:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                    box-shadow: 0 0 0 3px var(--accent-glow);
                }

                .table-wrapper { padding: 0; overflow: hidden; }
                .outage-table { width: 100%; border-collapse: collapse; text-align: left; }
                .outage-table th {
                    padding: 14px 20px;
                    background: var(--surface-hover);
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: var(--text-muted);
                    font-weight: 700;
                    border-bottom: 1px solid var(--border-color);
                }
                .outage-table td {
                    padding: 14px 20px;
                    border-bottom: 1px solid var(--border-color);
                    font-size: 0.85rem;
                }
                .operator-cell { font-weight: 700; color: var(--accent-primary); }
                .title-cell { font-weight: 500; }
                .location-cell { color: var(--text-secondary); }
                
                .service-tags-mini { display: flex; gap: 4px; flex-wrap: wrap; }
                .mini-tag {
                    font-size: 0.65rem;
                    background: var(--surface-hover);
                    padding: 2px 6px;
                    border-radius: 4px;
                    color: var(--text-secondary);
                    border: 1px solid var(--border-color);
                }
                .operator-cell { font-weight: 700; color: var(--accent-primary); }
                .title-cell { font-weight: 500; }
                .location-cell { color: var(--text-secondary); }
                
                .status-badge-mini {
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.65rem;
                    font-weight: 700;
                    text-transform: uppercase;
                }
                .status-badge-mini.active { color: var(--status-critical); border: 1px solid var(--status-critical); }
                .status-badge-mini.resolved { color: var(--status-success); border: 1px solid var(--status-success); }
                .status-badge-mini.investigating { color: var(--status-warning); border: 1px solid var(--status-warning); }
                
                .mini-tag.mobile {
                    background: rgba(0, 243, 255, 0.1);
                    color: #00f3ff;
                    border-color: #00f3ff;
                }

                .view-link {
                    color: var(--accent-primary);
                    text-decoration: none;
                    font-weight: 700;
                    font-size: 0.75rem;
                    text-transform: uppercase;
                }
                .view-link:hover { text-decoration: underline; }

                .empty-state { padding: 40px; text-align: center; color: var(--text-muted); }
                
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
                    .page-header { flex-direction: column; align-items: flex-start; }
                    .search-bar input { width: 100%; }
                    .outage-table th:nth-child(4), .outage-table td:nth-child(4) { display: none; }
                }
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
