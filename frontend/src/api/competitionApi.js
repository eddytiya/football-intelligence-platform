import apiClient from "./apiClient";


export const getCompetitions = async () => {

    const response = await apiClient.get("/competitions");

    return response.data;

};

export const getDecadeTopScorers = async (competitionId) => {
    const response = await apiClient.get(`/competitions/${competitionId}/top-scorers/decade`);
    return response.data;
};
