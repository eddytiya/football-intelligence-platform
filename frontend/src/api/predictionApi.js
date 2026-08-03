import apiClient from "./apiClient";

const predictionApi = {
    // ==========================================================
    // Today's Predictions
    // ==========================================================

    async getTodayPredictions() {
        const response = await apiClient.get("/predictions/today");
        return response.data;
    },

    // ==========================================================
    // Generate Prediction
    // ==========================================================

    async predictMatch(matchId) {
        const response = await apiClient.post(
            `/predictions/match/${matchId}`
        );

        return response.data;
    },

    // ==========================================================
    // Historical ML prediction
    // ==========================================================

    async getHistoricalPrediction(matchId) {
        const response = await apiClient.get(
            `/predictions/historical/match/${matchId}`
        );

        return response.data;
    },

    // ==========================================================
    // Prediction By Match
    // ==========================================================

    async getPrediction(matchId) {
        const response = await apiClient.get(
            `/predictions/match/${matchId}`
        );

        return response.data;
    },

    // ==========================================================
    // Competition Predictions
    // ==========================================================

    async getCompetitionPredictions(competitionId) {
        const response = await apiClient.get(
            `/predictions/competition/${competitionId}`
        );

        return response.data;
    },

    // ==========================================================
    // Delete Prediction
    // ==========================================================

    async deletePrediction(predictionId) {
        const response = await apiClient.delete(
            `/predictions/${predictionId}`
        );

        return response.data;
    },
};

export default predictionApi;
