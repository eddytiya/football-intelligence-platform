import apiClient from "./apiClient";

export const getNews = async ({ query = "", pageSize = "" } = {}) => {
    const response = await apiClient.get("/news", { params: { ...(query && { query }), ...(pageSize && { page_size: pageSize }) } });
    return response.data;
};
