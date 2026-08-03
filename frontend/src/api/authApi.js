import apiClient from "./apiClient";

export const login = async (email, password) => (await apiClient.post("/auth/login", { email, password })).data;
export const register = async (email, password) => (await apiClient.post("/auth/register", { email, password })).data;
