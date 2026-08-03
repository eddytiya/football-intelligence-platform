import apiClient from "./apiClient";

export const getDashboardSummary = async () => {
    const response = await apiClient.get("/dashboard/summary");
    return response.data;
};

export const getDashboardUpcomingMatches = async () => {
    const response = await apiClient.get("/dashboard/upcoming-matches");
    return response.data;
};

export const getDashboardRecentPredictions = async () => {
    const response = await apiClient.get("/dashboard/recent-predictions");
    return response.data;
};

export const getDashboardCommandCentre = async () => {
    const response = await apiClient.get("/dashboard/command-centre");
    return response.data;
};
