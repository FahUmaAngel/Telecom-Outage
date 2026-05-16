const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_TOKEN_STORAGE_KEY = "telecom-outage-auth-token";
let authToken = null;

const loadStoredAuthToken = () => {
    if (globalThis.window === undefined) {
        return null;
    }
    return globalThis.window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
};

const persistAuthToken = (token) => {
    if (globalThis.window === undefined) {
        return;
    }

    if (token) {
        globalThis.window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
    } else {
        globalThis.window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    }
};

const getAuthToken = () => {
    if (!authToken) {
        authToken = loadStoredAuthToken();
    }
    return authToken;
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
        if (response.status === 401) {
            authToken = null;
            persistAuthToken(null);
        }
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

            if (result.access_token) {
                authToken = result.access_token;
                persistAuthToken(result.access_token);
            }

            return result;
        },
        logout: () => {
            authToken = null;
            persistAuthToken(null);
        },
        getToken: () => getAuthToken(),
    },
    operators: {
        list: () => fetcher("/api/v1/operators"),
    },
    outages: {
        list: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            const queryString = query ? `?${query}` : "";
            return fetcher(`/api/v1/outages${queryString}`);
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
    research: {
        benchmarks: () => fetcher("/api/v1/research/benchmarks"),
        mttrPercentiles: (params) => fetcher("/api/v1/research/mttr-percentiles", { params }),
        mttrDistribution: (params) => fetcher("/api/v1/research/mttr-distribution", { params }),
        slaCompliance: (params) => fetcher("/api/v1/research/sla-compliance", { params }),
        valueScore: (params) => fetcher("/api/v1/research/value-score", { params }),
        statisticalTest: (params) => fetcher("/api/v1/research/statistical-test", { params }),
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
