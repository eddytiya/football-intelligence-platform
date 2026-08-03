import apiClient from "../api/apiClient";

const predictionService = {
    /**
     * Predict multiple matches.
     * @param {number[]} matchIds
     * @returns {Promise<Array>}
     */
    predictMatches: async (matchIds) => {
        const response = await apiClient.post(
            "/predictions/batch",
            {
                match_ids: matchIds,
            }
        );

        return response.data;
    },

    /**
     * Predict a single match.
     * @param {number} matchId
     * @returns {Promise<Object>}
     */
    predictMatch: async (matchId) => {
        const response = await apiClient.post(
            `/predictions/match/${matchId}`
        );

        return response.data;
    },
};

export default predictionService;
