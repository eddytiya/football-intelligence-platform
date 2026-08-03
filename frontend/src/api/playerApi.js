import apiClient from "./apiClient";

export const getPlayers = async ({ query = "", competitionId = "", position = "", limit = "", offset = "" } = {}) => {
    const response = await apiClient.get("/players", {
        params: {
            ...(query && { q: query }),
            ...(competitionId && { competition_id: competitionId }),
            ...(position && { position }),
            ...(limit && { limit }),
            ...(offset && { offset }),
        },
    });
    return response.data;
};

export const getPlayerPositions = async () => {
    const response = await apiClient.get("/players/positions");
    return response.data;
};
