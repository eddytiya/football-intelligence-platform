import axios from "axios";

// Vite exposes only variables prefixed with VITE_. Keeping the local URL as a
// fallback lets the app work in development while deployments can set the URL
// without changing source code.
export const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

apiClient.interceptors.request.use((config) => {
    try {
        const token = JSON.parse(localStorage.getItem("football-auth") || "null")?.access_token;
        if (token) config.headers.Authorization = `Bearer ${token}`;
    } catch { /* public endpoints continue without an account */ }
    return config;
});

export default apiClient;
