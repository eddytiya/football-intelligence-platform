import { fixtureDate } from "./fixturePresentation.js";
import { validProbabilities, verifiedTrainingCutoffs } from "./forecastTracker.js";

export const OBSERVATIONS_KEY = "football-forecast-observations";
const outcomes = ["home", "draw", "away"];
export function readObservations(storage = localStorage) {
  try {
    const rows = JSON.parse(storage.getItem(OBSERVATIONS_KEY) || "[]");
    return Array.isArray(rows)
      ? rows.filter(
          (row) =>
            row?.match_id &&
            verifiedTrainingCutoffs(row) &&
            validProbabilities(row.probabilities) &&
            fixtureDate(row.saved_at) &&
            fixtureDate(row.utc_date) > fixtureDate(row.saved_at),
        )
      : [];
  } catch {
    return [];
  }
}
export function forecastSnapshot(
  match,
  forecast,
  observedAt = new Date().toISOString(),
) {
  return {
    match_id: match.id,
    home_team: match.home_team_name,
    away_team: match.away_team_name,
    home_team_id: match.home_team_id,
    away_team_id: match.away_team_id,
    utc_date: match.utc_date,
    competition_name: match.competition_name,
    saved_at: observedAt,
    received_at: forecast.received_at || observedAt,
    model_version: forecast.model_version || null,
    leakage_protocol_version: forecast.leakage_protocol_version,
    training_data_through: forecast.training_data_through,
    history_through: forecast.history_through,
    probabilities: {
      home: forecast.home_win_probability,
      draw: forecast.draw_probability,
      away: forecast.away_win_probability,
    },
  };
}
export function recordObservation(
  snapshot,
  storage = localStorage,
  now = Date.now(),
) {
  if (
    !verifiedTrainingCutoffs(snapshot) ||
    !validProbabilities(snapshot.probabilities) ||
    !fixtureDate(snapshot.saved_at) ||
    fixtureDate(snapshot.utc_date)?.getTime() <= now ||
    fixtureDate(snapshot.saved_at)?.getTime() > now ||
    !fixtureDate(snapshot.utc_date)
  )
    return false;
  const rows = readObservations(storage);
  const same = rows.filter(
    (row) => String(row.match_id) === String(snapshot.match_id),
  );
  const previous = same.at(-1);
  if (
    previous &&
    fixtureDate(snapshot.saved_at) - fixtureDate(previous.saved_at) < 60000 &&
    previous.model_version === snapshot.model_version &&
    outcomes.every(
      (key) => previous.probabilities[key] === snapshot.probabilities[key],
    )
  )
    return true;
  const retain = same.slice(-199);
  const other = rows.filter(
    (row) => String(row.match_id) !== String(snapshot.match_id),
  );
  try {
    storage.setItem(
      OBSERVATIONS_KEY,
      JSON.stringify(
        [...other, ...retain, snapshot]
          .sort((a, b) => fixtureDate(a.saved_at) - fixtureDate(b.saved_at))
          .slice(-5000),
      ),
    );
    return true;
  } catch {
    return false;
  }
}
export function calibrationBins(rows, mode = "top") {
  const bins = Array.from({ length: 10 }, (_, index) => ({
    lower: index / 10,
    upper: (index + 1) / 10,
    count: 0,
    totalProbability: 0,
    correct: 0,
  }));
  for (const row of rows.filter((item) => item.state === "settled")) {
    const key =
      mode === "top"
        ? outcomes.reduce(
            (best, candidate) =>
              row.probabilities[candidate] > row.probabilities[best]
                ? candidate
                : best,
            "home",
          )
        : mode;
    if (!outcomes.includes(key)) continue;
    const probability = row.probabilities[key];
    const bin = bins[Math.min(9, Math.floor(probability * 10))];
    bin.count++;
    bin.totalProbability += probability;
    bin.correct += Number(row.actual === key);
  }
  return bins.map((bin) => ({
    ...bin,
    expected: bin.count ? bin.totalProbability / bin.count : null,
    observed: bin.count ? bin.correct / bin.count : null,
  }));
}
export function gameSummary(rows) {
  const settled = rows.filter((row) => row.state === "settled"),
    paired = settled.filter((row) => typeof row.model_correct === "boolean");
  return {
    total: settled.length,
    correct: settled.filter((row) => row.fan_correct).length,
    paired: paired.length,
    pairedFanCorrect: paired.filter((row) => row.fan_correct).length,
    pairedModelCorrect: paired.filter((row) => row.model_correct).length,
  };
}
