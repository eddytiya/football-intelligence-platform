import { useEffect, useState } from "react";
import predictionApi from "../api/predictionApi";
import apiClient from "../api/apiClient";
import { fixtureDate } from "../utils/fixturePresentation";
import { archiveForecast, verifiedTrainingCutoffs } from "../utils/forecastTracker";
import { forecastSnapshot, recordObservation } from "../utils/forecastEvidence";

const pending = new Map();
const recent = new Map();
function loadForecast(id) {
  const cached = recent.get(id);
  if (cached && Date.now() - cached.at < 120000)
    return Promise.resolve(cached.value);
  if (!pending.has(id)) {
    const request = predictionApi
      .getHistoricalPrediction(id)
      .then((value) => {
        const forecast = { ...value, received_at: new Date().toISOString() };
        if (forecast.prediction_status === "ready")
          recent.set(id, { at: Date.now(), value: forecast });
        return forecast;
      })
      .finally(() => pending.delete(id));
    pending.set(id, request);
  }
  return pending.get(id);
}

export default function useFixtureForecast(match, { adminReview = false } = {}) {
  const [state, setState] = useState({
    forecast: null,
    loading: false,
    error: "",
    saved: null,
  });
  const id = match?.id,
    kickoff = match?.utc_date,
    status = match?.status;
  const home = match?.home_team_name,
    away = match?.away_team_name;
  useEffect(() => {
    let active = true;
    const date = fixtureDate(kickoff);
    let history;
    try {
      history = JSON.parse(localStorage.getItem("prediction-history") || "[]");
      if (!Array.isArray(history)) history = [];
    } catch {
      history = [];
    }
    const saved =
      history.find((row) => String(row.match_id) === String(id) && verifiedTrainingCutoffs(row, kickoff)) || null;
    if (!id) {
      setState({
        forecast: null,
        loading: false,
        error: "Choose a fixture to explore its forecast.",
        saved: null,
      });
      return;
    }
    if (adminReview === null) {
      setState({ forecast: null, loading: true, error: "", saved });
      return;
    }
    if (adminReview) {
      setState({ forecast: null, loading: true, error: "", saved });
      apiClient.post(`/admin/predictions/match/${id}/review`)
        .then(({ data: review }) => {
          if (!active) return;
          setState({
            forecast: { ...review.forecast, generated_at: review.generated_at },
            review,
            loading: false,
            error: "",
            saved,
          });
        })
        .catch((error) => active && setState({ forecast: null, loading: false, saved,
          error: error.response?.data?.detail || "Admin forecast review is temporarily unavailable. Reload to try again." }));
      return () => { active = false; };
    }
    if (
      !date ||
      date.getTime() <= Date.now() ||
      !["SCHEDULED", "TIMED"].includes(status)
    ) {
      setState({
        forecast: null,
        loading: false,
        error:
          "New forecasts are available only for verified upcoming fixtures. Saved pre-match forecasts are preserved below.",
        saved,
      });
      return;
    }
    setState({ forecast: null, loading: true, error: "", saved });
    loadForecast(id)
      .then((forecast) => {
        if (!active) return;
        if (date.getTime() <= Date.now())
          throw new Error(
            "Kick-off has passed. New pre-match forecasts are no longer available.",
          );
        if (forecast.prediction_status !== "ready")
          throw new Error(
            "Verified team history is unavailable for this fixture.",
          );
        const observation = forecastSnapshot({id, utc_date:kickoff, home_team_name:home, away_team_name:away, home_team_id:match?.home_team_id, away_team_id:match?.away_team_id, competition_name:match?.competition_name}, forecast);
        recordObservation(observation);
        let current;
        try {
          current = JSON.parse(
            localStorage.getItem("prediction-history") || "[]",
          );
          if (!Array.isArray(current)) current = [];
        } catch {
          current = [];
        }
        if (
          !current.some((row) => String(row.match_id) === String(id)) &&
          date.getTime() > Date.now()
        ) {
          const snapshot = {
            match_id: id,
            home_team_id: match.home_team_id,
            away_team_id: match.away_team_id,
            competition_name: match.competition_name,
            home_team: home,
            away_team: away,
            utc_date: kickoff,
            predicted_outcome: forecast.predicted_outcome,
            likely_score:
              forecast.score_prediction?.most_likely_score?.score || null,
            saved_at: observation.saved_at,
            model_version: forecast.model_version,
            leakage_protocol_version: forecast.leakage_protocol_version,
            training_data_through: forecast.training_data_through,
            history_through: forecast.history_through,
            probabilities: {
              home: forecast.home_win_probability,
              draw: forecast.draw_probability,
              away: forecast.away_win_probability,
            },
          };
          archiveForecast(snapshot);
          try {
            localStorage.setItem(
              "prediction-history",
              JSON.stringify([snapshot, ...current].slice(0, 30)),
            );
          } catch {
            /* Reading a forecast still works if browser storage is full. */
          }
        }
        setState({ forecast, loading: false, error: "", saved });
      })
      .catch(
        (error) =>
          active &&
          setState({
            forecast: null,
            loading: false,
            error:
              error.response?.data?.detail ||
              error.message ||
              "The forecast is temporarily unavailable.",
            saved,
          }),
      );
    return () => {
      active = false;
    };
  }, [
    id,
    kickoff,
    status,
    home,
    away,
    match?.home_team_id,
    match?.away_team_id,
    match?.competition_name,
    adminReview,
  ]);
  return state;
}
