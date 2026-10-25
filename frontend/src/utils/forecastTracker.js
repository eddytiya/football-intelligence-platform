import { fixtureDate } from "./fixturePresentation.js";

export const ARCHIVE_KEY = "football-forecast-archive";
const outcomes = ["home", "draw", "away"];
export function verifiedTrainingCutoffs(row, kickoff = row?.utc_date) {
  const day = fixtureDate(kickoff)?.toISOString().slice(0, 10);
  return Boolean(day && row?.leakage_protocol_version === 1
    && /^\d{4}-\d{2}-\d{2}$/.test(row.training_data_through || "")
    && /^\d{4}-\d{2}-\d{2}$/.test(row.history_through || "")
    && row.training_data_through < day && row.history_through < day);
}
const read = (key, storage) => {
  try {
    const value = JSON.parse(storage.getItem(key) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
};

export function validProbabilities(probabilities) {
  const values = outcomes.map((key) => probabilities?.[key]);
  return (
    values.every(
      (value) =>
        typeof value === "number" &&
        Number.isFinite(value) &&
        value >= 0 &&
        value <= 1,
    ) && Math.abs(values.reduce((sum, value) => sum + value, 0) - 1) <= 0.0001
  );
}

export function readForecastArchive(storage = localStorage) {
  const unique = new Map();
  for (const row of [
    ...read(ARCHIVE_KEY, storage),
    ...read("prediction-history", storage),
  ]) {
    if (
      !row ||
      !Number.isInteger(Number(row.match_id)) ||
      Number(row.match_id) <= 0
    )
      continue;
    const saved = fixtureDate(row.saved_at),
      kickoff = fixtureDate(row.utc_date);
    if (
      !saved ||
      !kickoff ||
      saved >= kickoff ||
      !validProbabilities(row.probabilities)
    )
      continue;
    const key = String(row.match_id),
      previous = unique.get(key);
    if (!previous || (verifiedTrainingCutoffs(row) && !verifiedTrainingCutoffs(previous))
      || (verifiedTrainingCutoffs(row) === verifiedTrainingCutoffs(previous) && saved < fixtureDate(previous.saved_at)))
      unique.set(key, row);
  }
  return [...unique.values()].sort(
    (a, b) => fixtureDate(b.saved_at) - fixtureDate(a.saved_at),
  );
}

export function archiveForecast(snapshot, storage = localStorage) {
  const archive = readForecastArchive(storage);
  const previous = archive.findIndex((row) => String(row.match_id) === String(snapshot.match_id));
  if (previous >= 0 && !verifiedTrainingCutoffs(archive[previous]) && verifiedTrainingCutoffs(snapshot)) archive[previous] = snapshot;
  if (
    !archive.some((row) => String(row.match_id) === String(snapshot.match_id))
  )
    archive.push(snapshot);
  try {
    storage.setItem(ARCHIVE_KEY, JSON.stringify(archive));
    return true;
  } catch {
    return false;
  }
}

export function classifyForecast(snapshot, match, now = Date.now()) {
  if (!match)
    return {
      ...snapshot,
      state: "unavailable",
      reason: "Result could not be checked",
    };
  const kickoff = fixtureDate(match.utc_date),
    saved = fixtureDate(snapshot.saved_at);
  const base = {
    ...snapshot,
    match,
    league: match.competition_name || "Unknown competition",
  };
  if (!verifiedTrainingCutoffs(snapshot, match.utc_date))
    return { ...base, state: "excluded", reason: "Training or feature cutoff is unverified; excluded from performance." };
  if (
    !kickoff ||
    !saved ||
    saved >= kickoff ||
    !validProbabilities(snapshot.probabilities)
  )
    return {
      ...base,
      state: "excluded",
      reason: "Pre-match timing or probabilities cannot be verified",
    };
  if (
    (snapshot.home_team_id &&
      Number(snapshot.home_team_id) !== Number(match.home_team_id)) ||
    (snapshot.away_team_id &&
      Number(snapshot.away_team_id) !== Number(match.away_team_id))
  )
    return {
      ...base,
      state: "excluded",
      reason: "Fixture club identity changed",
    };
  if (match.status !== "FINISHED")
    return {
      ...base,
      state: "pending",
      reason: match.status || "Awaiting final result",
    };
  if (
    kickoff.getTime() > now ||
    ![match.home_score, match.away_score].every(
      (value) => Number.isInteger(value) && value >= 0,
    )
  )
    return {
      ...base,
      state: "excluded",
      reason: "Final result or kickoff requires verification",
    };
  const actual =
    match.home_score > match.away_score
      ? "home"
      : match.home_score < match.away_score
        ? "away"
        : "draw";
  const maximum = Math.max(
    ...outcomes.map((key) => snapshot.probabilities[key]),
  );
  const leaders = outcomes.filter(
    (key) => snapshot.probabilities[key] === maximum,
  );
  const picked = leaders[0];
  return {
    ...base,
    state: "settled",
    actual,
    picked,
    tied: leaders.length > 1,
    correct: picked === actual,
    loss: -Math.log(Math.max(1e-15, snapshot.probabilities[actual])),
  };
}

export function scoreForecasts(rows) {
  const settled = rows.filter((row) => row.state === "settled");
  const correct = settled.filter((row) => row.correct).length;
  const actualDraws = settled.filter((row) => row.actual === "draw").length;
  const selectedDraws = settled.filter((row) => row.picked === "draw").length;
  const correctDraws = settled.filter(
    (row) => row.picked === "draw" && row.actual === "draw",
  ).length;
  return {
    count: settled.length,
    correct,
    accuracy: settled.length ? correct / settled.length : null,
    logLoss: settled.length
      ? settled.reduce((sum, row) => sum + row.loss, 0) / settled.length
      : null,
    actualDraws,
    selectedDraws,
    correctDraws,
    drawRecall: actualDraws ? correctDraws / actualDraws : null,
    drawPrecision: selectedDraws ? correctDraws / selectedDraws : null,
  };
}

export async function reconcileForecasts(snapshots, getMatch) {
  const rows = new Array(snapshots.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(4, snapshots.length) }, async () => {
      while (next < snapshots.length) {
        const index = next++;
        try {
          rows[index] = classifyForecast(
            snapshots[index],
            await getMatch(snapshots[index].match_id),
          );
        } catch {
          rows[index] = classifyForecast(snapshots[index], null);
        }
      }
    }),
  );
  return rows;
}
