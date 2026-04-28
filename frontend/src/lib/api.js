const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getAuthToken = () => {
    if (typeof window === "undefined") {
        return null;
    }

    return window.localStorage.getItem("auth_token");
};

const fetcher = async (endpoint, options = {}) => {
    let url = `${BASE_URL}${endpoint}`;

    if (options.params) {
        const query = new URLSearchParams(options.params).toString();
        if (query) {
            url += (url.includes("?") ? "&" : "?") + query;
        }
    }

    const token = getAuthToken();
    const hasBody = options.body !== undefined;

    const response = await fetch(url, {
        ...options,
        headers: {
            ...(hasBody ? { "Content-Type": "application/json" } : {}),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || error.message || "Something went wrong");
    }

    if (response.status === 204) {
        return null;
    }

    return response.json().catch(() => null);
};

export const api = {
    auth: {
        login: async (username, password) => {
            const body = new URLSearchParams({ username, password });
            const response = await fetch(`${BASE_URL}/api/v1/auth/token`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: body.toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.detail || "Unable to sign in");
            }

            if (typeof window !== "undefined" && result.access_token) {
                window.localStorage.setItem("auth_token", result.access_token);
            }

            return result;
        },
        logout: () => {
            if (typeof window !== "undefined") {
                window.localStorage.removeItem("auth_token");
            }
        },
    },
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
                const queryString = query ? `?${query}` : "";
                return fetcher(`/api/v1/admin/outages${queryString}`);
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
