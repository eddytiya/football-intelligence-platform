import apiClient from "./apiClient";

export const getTeams = async ({ query = "", competitionId = "", limit = "", offset = "" } = {}) => {
    const response = await apiClient.get("/teams", { params: { ...(query && { q: query }), ...(competitionId && { competition_id: competitionId }), ...(limit && { limit }), ...(offset && { offset }) } });
    return response.data;
};

export const getTeamProfile = async (teamId) => {
    const response = await apiClient.get(`/teams/${teamId}`);
    return response.data;
};

export const getTeamComparison = async (firstTeamId, secondTeamId) => {
    const response = await apiClient.get("/teams/compare", { params: { first_team_id: firstTeamId, second_team_id: secondTeamId } });
    return response.data;
};
