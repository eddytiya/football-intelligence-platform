import apiClient from "./apiClient";
export const getFanPicks = () =>
  apiClient.get("/fan-game/picks", { timeout: 15000 }).then(({ data }) => data);
export const submitFanPick = (match_id, outcome) =>
  apiClient
    .post("/fan-game/picks", { match_id, outcome }, { timeout: 60000 })
    .then(({ data }) => data);
