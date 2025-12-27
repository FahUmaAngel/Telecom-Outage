const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const fetcher = async (endpoint, options = {}) => {
    const url = `${BASE_URL}${endpoint}`;
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
        list: () => fetcher("/operators"),
    },
    outages: {
        list: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            return fetcher(`/outages${query ? `?${query}` : ""}`);
        },
        get: (id) => fetcher(`/outages/${id}`),
        history: () => fetcher("/analytics/history"),
        reliability: () => fetcher("/analytics/reliability"),
        mttr: () => fetcher("/analytics/mttr"),
    },
    reports: {
        list: () => fetcher("/reports"),
        hotspots: () => fetcher("/reports/hotspots"),
        create: (data) => fetcher("/reports", {
            method: "POST",
            body: JSON.stringify(data),
        }),
    },
    regions: {
        list: () => fetcher("/regions"),
    },
    admin: {
        scrapers: () => fetcher("/admin/scrapers"),
        reports: {
            list: () => fetcher("/reports"), // Use common reports list
            verify: (id) => fetcher(`/admin/reports/${id}/verify`, { method: "POST" }),
            reject: (id) => fetcher(`/admin/reports/${id}/reject`, { method: "POST" }),
        }
    }
};
