const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fetcher = async (endpoint, options = {}) => {
    let url = `${BASE_URL}${endpoint}`;

    if (options.params) {
        const query = new URLSearchParams(options.params).toString();
        if (query) {
            url += (url.includes("?") ? "&" : "?") + query;
        }
    }

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || "Something went wrong");
    }

    return response.json();
};

export const api = {
    operators: {
        list: () => fetcher("/api/v1/operators"),
    },
    outages: {
        list: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            return fetcher(`/api/v1/outages${query ? `?${query}` : ""}`);
        },
        get: (id) => fetcher(`/api/v1/outages/${id}`),
        history: () => fetcher("/api/v1/analytics/history"),
        reliability: (params) => fetcher("/api/v1/analytics/reliability", { params }),
        mttr: (params) => fetcher("/api/v1/analytics/mttr", { params }),
        mttrDynamic: (params) => fetcher("/api/v1/analytics/mttr-dynamic", { params }),
        locations: (params) => fetcher("/api/v1/analytics/locations", { params }),
    },
    reports: {
        list: () => fetcher("/api/v1/reports"),
        hotspots: () => fetcher("/api/v1/reports/hotspots"),
        create: (data) => fetcher("/api/v1/reports", {
            method: "POST",
            body: JSON.stringify(data),
        }),
    },
    regions: {
        list: () => fetcher("/api/v1/regions"),
    },
    admin: {
        scrapers: () => fetcher("/api/v1/admin/scrapers"),
        outages: {
            list: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return fetcher(`/api/v1/admin/outages${query ? `?${query}` : ""}`);
            },
            update: (id, data) => fetcher(`/api/v1/admin/outages/${id}`, {
                method: "PUT",
                body: JSON.stringify(data),
            }),
            resolvePlace: (query) => fetcher(`/api/v1/admin/resolve-place`, { method: 'POST', body: JSON.stringify({ query }) }),
        },
        reports: {
            list: () => fetcher("/api/v1/reports"),
            verify: (id) => fetcher(`/api/v1/admin/reports/${id}/verify`, { method: "POST" }),
            reject: (id) => fetcher(`/api/v1/admin/reports/${id}/reject`, { method: "POST" }),
        }
    }
};
