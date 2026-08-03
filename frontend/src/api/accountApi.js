import apiClient from "./apiClient";

export const getAccountFavourites = () => apiClient.get("/auth/favourites").then(({ data }) => data);
export const saveAccountFavourite = (entity_type, entity_id) => apiClient.post("/auth/favourites", { entity_type, entity_id }).then(({ data }) => data);
export const removeAccountFavourite = (entity_type, entity_id) => apiClient.delete(`/auth/favourites/${entity_type}/${entity_id}`);
export const getWatchlist = () => apiClient.get("/auth/watchlist").then(({ data }) => data);
export const saveWatchlist = (match_id, reminder_minutes = 60) => apiClient.post("/auth/watchlist", { match_id, reminder_minutes }).then(({ data }) => data);
export const removeWatchlist = (match_id) => apiClient.delete(`/auth/watchlist/${match_id}`);
