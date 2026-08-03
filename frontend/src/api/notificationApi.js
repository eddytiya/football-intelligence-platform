import apiClient from "./apiClient";

export const getNotifications = async () => {
    const response = await apiClient.get("/notifications");
    return response.data;
};

export const markNotificationRead = async (notificationId) => {
    const response = await apiClient.post(`/notifications/${notificationId}/read`);
    return response.data;
};

export const markAllNotificationsRead = async () => {
    const response = await apiClient.post("/notifications/read-all");
    return response.data;
};
