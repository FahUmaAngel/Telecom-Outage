"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import { useLanguage } from "../../context/LanguageContext";
import { useToast } from "../../context/ToastContext";

const PAGE_SIZE = 100;
const EMPTY_FORM = {
    incident_id: "",
    operator_id: "",
    region_id: "",
    raw_data_id: "",
    title_sv: "",
    title_en: "",
    description_sv: "",
    description_en: "",
    status: "active",
    severity: "unknown",
    start_time: "",
    end_time: "",
    estimated_fix_time: "",
    latitude: "",
    longitude: "",
    location: "",
    place: "",
    affected_services: [],
};

function toLocalDateTime(value) {
    if (!value) return "";
    return new Date(value).toISOString().slice(0, 16);
}

export default function AdminPage() {
    const { lang } = useLanguage();
    const { addToast } = useToast();
    const [loading, setLoading] = useState(false);
    const [scrapers, setScrapers] = useState([]);
    const [reports, setReports] = useState([]);
    const [outages, setOutages] = useState([]);
    const [outagesLoading, setOutagesLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [filterOperator, setFilterOperator] = useState("");
    const [filterStatus, setFilterStatus] = useState("");
    const [filterMissingCoords, setFilterMissingCoords] = useState(false);
    const [filterMissingEndDate, setFilterMissingEndDate] = useState(false);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [editingOutage, setEditingOutage] = useState(null);
    const [editForm, setEditForm] = useState(EMPTY_FORM);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [authLoading, setAuthLoading] = useState(false);
    const [credentials, setCredentials] = useState({ username: "", password: "" });

    const loadAdminData = async () => {
        const [scrapersData, reportsData] = await Promise.all([
            api.admin.scrapers(),
            api.admin.reports.list(),
        ]);
        setScrapers(scrapersData);
        setReports(reportsData);
    };

    const loadOutages = async (nextPage = 0, overrides = {}) => {
        setOutagesLoading(true);
        try {
            const params = {
                limit: PAGE_SIZE,
                offset: nextPage * PAGE_SIZE,
                ...(overrides.search ?? searchQuery ? { search: overrides.search ?? searchQuery } : {}),
                ...(overrides.operator ?? filterOperator ? { operator: overrides.operator ?? filterOperator } : {}),
                ...(overrides.status ?? filterStatus ? { status: overrides.status ?? filterStatus } : {}),
                ...((overrides.missingCoords ?? filterMissingCoords) ? { missing_coords: true } : {}),
                ...((overrides.missingEndDate ?? filterMissingEndDate) ? { missing_end_date: true } : {}),
            };

            const data = await api.admin.outages.list(params);
            setOutages(data);
            setHasMore(data.length === PAGE_SIZE);
        } catch (error) {
            addToast(
                lang === "sv" ? "Kunde inte hamta driftstorningar" : "Failed to fetch outages",
                "error"
            );
        } finally {
            setOutagesLoading(false);
        }
    };

    const loadAdminPage = async () => {
        setLoading(true);
        try {
            await Promise.all([loadAdminData(), loadOutages(0)]);
        } catch (error) {
            const message = error.message || "";
            if (message.toLowerCase().includes("credentials") || message.toLowerCase().includes("unauthorized")) {
                api.auth.logout();
                setIsAuthenticated(false);
                addToast(
                    lang === "sv" ? "Sessionen gick ut. Logga in igen." : "Your session expired. Please sign in again.",
                    "error"
                );
            } else {
                addToast(
                    lang === "sv" ? "Kunde inte hamta admin-data" : "Failed to load admin data",
                    "error"
                );
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const token = api.auth.getToken();
        if (token) {
            setIsAuthenticated(true);
            loadAdminPage();
        }
    }, []);

    const scraperCards = useMemo(
        () => scrapers.filter((item) => item.operator !== "tele2"),
        [scrapers]
    );

    const applyFilters = (updates = {}) => {
        const nextSearch = updates.search ?? searchQuery;
        const nextOperator = updates.operator ?? filterOperator;
        const nextStatus = updates.status ?? filterStatus;
        const nextMissingCoords = updates.missingCoords ?? filterMissingCoords;
        const nextMissingEndDate = updates.missingEndDate ?? filterMissingEndDate;

        setPage(0);
        loadOutages(0, {
            search: nextSearch,
            operator: nextOperator,
            status: nextStatus,
            missingCoords: nextMissingCoords,
            missingEndDate: nextMissingEndDate,
        });
    };

    const openEditor = (outage) => {
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
            status: outage.status || "active",
            severity: outage.severity || "unknown",
            start_time: toLocalDateTime(outage.start_time),
            end_time: toLocalDateTime(outage.end_time),
            estimated_fix_time: toLocalDateTime(outage.estimated_fix_time),
            latitude: outage.latitude ?? "",
            longitude: outage.longitude ?? "",
            location: outage.location || "",
            place: outage.place || "",
            affected_services: outage.affected_services || [],
        });
    };

    const closeEditor = () => {
        setEditingOutage(null);
        setEditForm(EMPTY_FORM);
    };

    const handleLogin = async (event) => {
        event.preventDefault();
        setAuthLoading(true);
        try {
            await api.auth.login(credentials.username, credentials.password);
            setIsAuthenticated(true);
            addToast(lang === "sv" ? "Inloggning lyckades" : "Signed in", "success");
            await loadAdminPage();
        } catch (error) {
            addToast(error.message || (lang === "sv" ? "Inloggning misslyckades" : "Sign-in failed"), "error");
        } finally {
            setAuthLoading(false);
        }
    };

    const handleLogout = () => {
        api.auth.logout();
        setIsAuthenticated(false);
        setScrapers([]);
        setReports([]);
        setOutages([]);
        setEditingOutage(null);
        setPage(0);
        addToast(lang === "sv" ? "Utloggad" : "Signed out", "success");
    };

    const handleReportAction = async (id, action) => {
        try {
            if (action === "verify") {
                await api.admin.reports.verify(id);
            } else {
                await api.admin.reports.reject(id);
            }
            addToast(lang === "sv" ? "Rapport uppdaterad" : "Report updated", "success");
            await loadAdminData();
        } catch (error) {
            addToast(lang === "sv" ? "Kunde inte uppdatera rapport" : "Failed to update report", "error");
        }
    };

    const handleResolvePlace = async () => {
        if (!editForm.place) return;
        try {
            const data = await api.admin.outages.resolvePlace(editForm.place);
            setEditForm((current) => ({
                ...current,
                latitude: data.latitude,
                longitude: data.longitude,
                location: data.display_name,
                region_id: data.region_id || current.region_id,
            }));
            addToast(lang === "sv" ? "Plats identifierad" : "Place resolved", "success");
        } catch (error) {
            addToast(lang === "sv" ? "Kunde inte hitta platsen" : "Failed to resolve place", "error");
        }
    };

    const handleUpdateOutage = async (event) => {
        event.preventDefault();
        if (!editingOutage) return;

        try {
            await api.admin.outages.update(editingOutage.id, {
                incident_id: editForm.incident_id || null,
                operator_id: editForm.operator_id ? Number.parseInt(editForm.operator_id, 10) : null,
                region_id: editForm.region_id ? Number.parseInt(editForm.region_id, 10) : null,
                raw_data_id: editForm.raw_data_id ? Number.parseInt(editForm.raw_data_id, 10) : null,
                title: { sv: editForm.title_sv, en: editForm.title_en },
                description: { sv: editForm.description_sv, en: editForm.description_en },
                status: editForm.status,
                severity: editForm.severity,
                start_time: editForm.start_time || null,
                end_time: editForm.end_time || null,
                estimated_fix_time: editForm.estimated_fix_time || null,
                latitude: editForm.latitude !== "" ? Number.parseFloat(editForm.latitude) : null,
                longitude: editForm.longitude !== "" ? Number.parseFloat(editForm.longitude) : null,
                location: editForm.location || null,
                place: editForm.place || null,
                affected_services: editForm.affected_services,
            });

            addToast(lang === "sv" ? "Driftstorning uppdaterad" : "Outage updated", "success");
            closeEditor();
            await loadOutages(page);
        } catch (error) {
            addToast(lang === "sv" ? "Kunde inte uppdatera" : "Failed to update", "error");
        }
    };

    if (!isAuthenticated) {
        return (
            <div style={{ padding: 24, maxWidth: 480, margin: "48px auto" }}>
                <h1 style={{ marginBottom: 8 }}>{lang === "sv" ? "Administration" : "Admin"}</h1>
                <p style={{ marginBottom: 24, opacity: 0.75 }}>
                    {lang === "sv"
                        ? "Logga in med ett administratorkonto for att fortsatta."
                        : "Sign in with an administrator account to continue."}
                </p>
                <form
                    onSubmit={handleLogin}
                    style={{ display: "grid", gap: 12, padding: 20, border: "1px solid var(--border-color)", borderRadius: 8 }}
                >
                    <input
                        value={credentials.username}
                        onChange={(event) => setCredentials((current) => ({ ...current, username: event.target.value }))}
                        placeholder="Username"
                        autoComplete="username"
                    />
                    <input
                        type="password"
                        value={credentials.password}
                        onChange={(event) => setCredentials((current) => ({ ...current, password: event.target.value }))}
                        placeholder="Password"
                        autoComplete="current-password"
                    />
                    <button type="submit" disabled={authLoading}>
                        {authLoading
                            ? (lang === "sv" ? "Loggar in..." : "Signing in...")
                            : (lang === "sv" ? "Logga in" : "Sign in")}
                    </button>
                    <p style={{ margin: 0, fontSize: 14, opacity: 0.75 }}>
                        {lang === "sv"
                            ? "I lokal utveckling skapas standardkontot admin automatiskt när inga användare finns. Kontrollera miljövariablerna för lösenordet."
                            : "In local development, a default admin account is created automatically when no users exist. Check environment variables for the password."}
                    </p>
                </form>
            </div>
        );
    }

    if (loading) {
        return <div style={{ padding: 24 }}>Loading...</div>;
    }

    return (
        <div style={{ padding: 24, maxWidth: 1280, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 8 }}>
                <h1 style={{ margin: 0 }}>{lang === "sv" ? "Administration" : "Admin"}</h1>
                <button type="button" onClick={handleLogout}>
                    {lang === "sv" ? "Logga ut" : "Sign out"}
                </button>
            </div>
            <p style={{ marginBottom: 24, opacity: 0.75 }}>
                {lang === "sv" ? "Moderering och datakvalitet" : "Moderation and data quality"}
            </p>

            <section style={{ marginBottom: 32 }}>
                <h2>{lang === "sv" ? "Scraper-status" : "Scraper status"}</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
                    {scraperCards.map((item) => {
                        const stale = new Date() - new Date(item.last_scraped_at) >= 3600000;
                        return (
                            <div key={item.operator} style={{ border: "1px solid var(--border-color)", borderRadius: 8, padding: 16 }}>
                                <div style={{ fontWeight: 700 }}>{item.operator.toUpperCase()}</div>
                                <div style={{ color: stale ? "#f59e0b" : "#10b981" }}>
                                    {stale ? "stale" : "online"}
                                </div>
                                <div style={{ opacity: 0.75 }}>{new Date(item.last_scraped_at).toLocaleString()}</div>
                            </div>
                        );
                    })}
                </div>
            </section>

            <section style={{ marginBottom: 32 }}>
                <h2>{lang === "sv" ? "Rapporter" : "Reports"}</h2>
                <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr>
                                <th align="left">ID</th>
                                <th align="left">{lang === "sv" ? "Operator" : "Operator"}</th>
                                <th align="left">{lang === "sv" ? "Titel" : "Title"}</th>
                                <th align="left">{lang === "sv" ? "Status" : "Status"}</th>
                                <th align="left">{lang === "sv" ? "Atgard" : "Action"}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reports.map((report) => (
                                <tr key={report.id}>
                                    <td>{report.id}</td>
                                    <td>{report.operator_name || "-"}</td>
                                    <td>{report.title}</td>
                                    <td>{report.status}</td>
                                    <td>
                                        {report.status === "pending" ? (
                                            <div style={{ display: "flex", gap: 8 }}>
                                                <button onClick={() => handleReportAction(report.id, "verify")}>Verify</button>
                                                <button onClick={() => handleReportAction(report.id, "reject")}>Reject</button>
                                            </div>
                                        ) : "Processed"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            <section style={{ marginBottom: 32 }}>
                <h2>{lang === "sv" ? "Driftstorningar" : "Outages"}</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 16 }}>
                    <input
                        value={searchQuery}
                        onChange={(event) => setSearchQuery(event.target.value)}
                        onBlur={() => applyFilters({ search: searchQuery })}
                        placeholder={lang === "sv" ? "Sok..." : "Search..."}
                    />
                    <select
                        value={filterOperator}
                        onChange={(event) => {
                            setFilterOperator(event.target.value);
                            applyFilters({ operator: event.target.value });
                        }}
                    >
                        <option value="">{lang === "sv" ? "Alla operatorer" : "All operators"}</option>
                        <option value="telia">Telia</option>
                        <option value="telenor">Telenor</option>
                        <option value="tre">Tre</option>
                    </select>
                    <select
                        value={filterStatus}
                        onChange={(event) => {
                            setFilterStatus(event.target.value);
                            applyFilters({ status: event.target.value });
                        }}
                    >
                        <option value="">{lang === "sv" ? "Alla statusar" : "All statuses"}</option>
                        <option value="active">active</option>
                        <option value="resolved">resolved</option>
                        <option value="scheduled">scheduled</option>
                    </select>
                    <label>
                        <input
                            type="checkbox"
                            checked={filterMissingCoords}
                            onChange={(event) => {
                                setFilterMissingCoords(event.target.checked);
                                applyFilters({ missingCoords: event.target.checked });
                            }}
                        />
                        {" "}
                        {lang === "sv" ? "Saknar koordinater" : "Missing coords"}
                    </label>
                    <label>
                        <input
                            type="checkbox"
                            checked={filterMissingEndDate}
                            onChange={(event) => {
                                setFilterMissingEndDate(event.target.checked);
                                applyFilters({ missingEndDate: event.target.checked });
                            }}
                        />
                        {" "}
                        {lang === "sv" ? "Saknar slutdatum" : "Missing end date"}
                    </label>
                </div>

                <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr>
                                <th align="left">ID</th>
                                <th align="left">{lang === "sv" ? "Operator" : "Operator"}</th>
                                <th align="left">{lang === "sv" ? "Titel" : "Title"}</th>
                                <th align="left">{lang === "sv" ? "Plats" : "Location"}</th>
                                <th align="left">{lang === "sv" ? "Status" : "Status"}</th>
                                <th align="left">{lang === "sv" ? "Kvalitet" : "Quality"}</th>
                                <th align="left">{lang === "sv" ? "Atgard" : "Action"}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {outages.map((outage) => (
                                <tr key={outage.id}>
                                    <td>{outage.id}</td>
                                    <td>{outage.operator_name}</td>
                                    <td>{outage.title?.sv || outage.title?.en || "-"}</td>
                                    <td>{outage.location || "-"}</td>
                                    <td>{outage.status}</td>
                                    <td>{outage.quality_issues?.join(", ") || "OK"}</td>
                                    <td>
                                        <button onClick={() => openEditor(outage)}>Edit</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
                    <button
                        disabled={page === 0 || outagesLoading}
                        onClick={() => {
                            const nextPage = page - 1;
                            setPage(nextPage);
                            loadOutages(nextPage);
                        }}
                    >
                        Previous
                    </button>
                    <span>{lang === "sv" ? `Sida ${page + 1}` : `Page ${page + 1}`}</span>
                    <button
                        disabled={!hasMore || outagesLoading}
                        onClick={() => {
                            const nextPage = page + 1;
                            setPage(nextPage);
                            loadOutages(nextPage);
                        }}
                    >
                        Next
                    </button>
                </div>
            </section>

            {editingOutage && (
                <section style={{ border: "1px solid var(--border-color)", borderRadius: 8, padding: 16 }}>
                    <h2>{lang === "sv" ? "Redigera driftstorning" : "Edit outage"} #{editingOutage.id}</h2>
                    <form onSubmit={handleUpdateOutage} style={{ display: "grid", gap: 12 }}>
                        <input value={editForm.incident_id} onChange={(event) => setEditForm({ ...editForm, incident_id: event.target.value })} placeholder="Incident ID" />
                        <input value={editForm.title_sv} onChange={(event) => setEditForm({ ...editForm, title_sv: event.target.value })} placeholder="Title (sv)" />
                        <input value={editForm.title_en} onChange={(event) => setEditForm({ ...editForm, title_en: event.target.value })} placeholder="Title (en)" />
                        <textarea value={editForm.description_sv} onChange={(event) => setEditForm({ ...editForm, description_sv: event.target.value })} placeholder="Description (sv)" />
                        <textarea value={editForm.description_en} onChange={(event) => setEditForm({ ...editForm, description_en: event.target.value })} placeholder="Description (en)" />
                        <input value={editForm.place} onChange={(event) => setEditForm({ ...editForm, place: event.target.value })} placeholder="Place" />
                        <div style={{ display: "flex", gap: 8 }}>
                            <button type="button" onClick={handleResolvePlace}>Resolve place</button>
                            <button type="button" onClick={closeEditor}>Cancel</button>
                        </div>
                        <input value={editForm.location} onChange={(event) => setEditForm({ ...editForm, location: event.target.value })} placeholder="Location" />
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                            <input value={editForm.latitude} onChange={(event) => setEditForm({ ...editForm, latitude: event.target.value })} placeholder="Latitude" />
                            <input value={editForm.longitude} onChange={(event) => setEditForm({ ...editForm, longitude: event.target.value })} placeholder="Longitude" />
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                            <select value={editForm.status} onChange={(event) => setEditForm({ ...editForm, status: event.target.value })}>
                                <option value="detecting">detecting</option>
                                <option value="active">active</option>
                                <option value="investigating">investigating</option>
                                <option value="identified">identified</option>
                                <option value="monitoring">monitoring</option>
                                <option value="resolved">resolved</option>
                                <option value="scheduled">scheduled</option>
                            </select>
                            <select value={editForm.severity} onChange={(event) => setEditForm({ ...editForm, severity: event.target.value })}>
                                <option value="low">low</option>
                                <option value="medium">medium</option>
                                <option value="high">high</option>
                                <option value="critical">critical</option>
                                <option value="unknown">unknown</option>
                            </select>
                        </div>
                        <button type="submit">{lang === "sv" ? "Spara" : "Save"}</button>
                    </form>
                </section>
            )}
        </div>
    );
}
