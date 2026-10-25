import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import { readObservations } from "../utils/forecastEvidence";
import { readForecastArchive } from "../utils/forecastTracker";
import { fixtureDate, kickoffLabel } from "../utils/fixturePresentation";
import "../styles/fan-features.css";

const sides = ["home", "draw", "away"],
  labels = { home: "Home win", draw: "Draw", away: "Away win" };
export default function ForecastMovement() {
  const [params, setParams] = useSearchParams(),
    [, setRefresh] = useState(0);
  const records = (() => {
    const rows = readObservations();
    for (const snapshot of readForecastArchive())
      if (
        !rows.some(
          (row) =>
            String(row.match_id) === String(snapshot.match_id) &&
            row.saved_at === snapshot.saved_at,
        )
      )
        rows.push({ ...snapshot, legacy: true });
    return rows.sort(
      (a, b) => fixtureDate(a.saved_at) - fixtureDate(b.saved_at),
    );
  })();
  const matches = [
    ...new Map(records.map((row) => [String(row.match_id), row])).values(),
  ];
  const selected =
    params.get("match") || String(matches.at(-1)?.match_id || "");
  const observations = records.filter(
      (row) => String(row.match_id) === selected,
    ),
    first = observations[0],
    last = observations.at(-1);
  const versions = new Set(
    observations.map((row) => row.model_version || "Unrecorded"),
  );
  const start = first ? fixtureDate(first.saved_at).getTime() : 0,
    end = last ? fixtureDate(last.saved_at).getTime() : 1;
  return (
    <MainLayout>
      <section className="fan-page">
        <header className="fan-page-heading">
          <div>
            <h1>Forecast movement</h1>
            <p>How the probabilities looked at each recorded visit.</p>
          </div>
          <button
            className="flood-button subtle"
            onClick={() => setRefresh((value) => value + 1)}
          >
            Reload saved observations
          </button>
        </header>
        <p className="fan-scope">
          Browser-local observations, captured when you open a verified upcoming
          forecast. This is not continuous monitoring or a bookmaker’s odds
          history. Observation time is when you viewed it; a cached forecast can
          have an earlier retrieval time.
        </p>
        <div className="fan-filters">
          <label>
            Match
            <select
              value={selected}
              onChange={(event) => setParams({ match: event.target.value })}
            >
              <option value="">Choose a saved match</option>
              {matches.map((row) => (
                <option value={row.match_id} key={row.match_id}>
                  {row.home_team} vs {row.away_team} ·{" "}
                  {kickoffLabel(row.utc_date)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {first ? (
          <>
            <h2>
              {first.home_team} vs {first.away_team}
            </h2>
            <p className="fan-scope">
              {observations.length} recorded observations ·{" "}
              {kickoffLabel(first.saved_at)} to {kickoffLabel(last.saved_at)}
              {versions.size > 1
                ? " · Model versions changed: movement includes model changes as well as any new data."
                : ""}
            </p>
            {observations.length > 1 ? (
              <>
                <div className="movement-deltas">
                  {sides.map((side) => (
                    <div key={side}>
                      <span>{labels[side]}</span>
                      <b>
                        {(first.probabilities[side] * 100).toFixed(1)}% →{" "}
                        {(last.probabilities[side] * 100).toFixed(1)}%
                      </b>
                      <small>
                        {(
                          (last.probabilities[side] -
                            first.probabilities[side]) *
                          100
                        ).toFixed(1)}{" "}
                        percentage points
                      </small>
                    </div>
                  ))}
                </div>
                <div className="evidence-plot">
                  <svg
                    viewBox="0 0 600 340"
                    role="img"
                    aria-label="Observed home, draw and away probabilities over time, with full values in the table below."
                  >
                    {[0, 0.5, 1].map((value) => (
                      <g key={value}>
                        <line
                          className="plot-axis"
                          x1="55"
                          y1={275 - 240 * value}
                          x2="560"
                          y2={275 - 240 * value}
                        />
                        <text x="45" y={280 - 240 * value} textAnchor="end">
                          {value * 100}%
                        </text>
                      </g>
                    ))}
                    {sides.map((side) => (
                      <polyline
                        key={side}
                        className={`movement-${side}`}
                        points={observations
                          .map(
                            (row) =>
                              `${55 + (505 * (fixtureDate(row.saved_at).getTime() - start)) / Math.max(1, end - start)},${275 - 240 * row.probabilities[side]}`,
                          )
                          .join(" ")}
                      />
                    ))}
                    <text x="55" y="310">
                      First observation
                    </text>
                    <text x="560" y="310" textAnchor="end">
                      Latest observation
                    </text>
                  </svg>
                  <div className="movement-legend">
                    {sides.map((side) => (
                      <span className={`movement-${side}`} key={side}>
                        {labels[side]}
                      </span>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="fan-empty">
                <h3>One observation is a starting point</h3>
                <p>
                  Reopen this forecast later, before kickoff, to record another
                  observation. There is no earlier movement history to
                  reconstruct.
                </p>
              </div>
            )}
            <div className="fan-actions">
              <Link className="flood-button" to={`/matches/${selected}`}>
                Open match forecast
              </Link>
              <Link className="flood-button subtle" to="/confidence-explorer">
                Explore confidence
              </Link>
            </div>
            <section className="fan-section">
              <h2>Recorded probabilities</h2>
              <div className="fan-table-scroll">
                <table className="fan-table">
                  <thead>
                    <tr>
                      <th>Observed</th>
                      <th>Home</th>
                      <th>Draw</th>
                      <th>Away</th>
                      <th>Model</th>
                    </tr>
                  </thead>
                  <tbody>
                    {observations.map((row, index) => (
                      <tr key={`${row.saved_at}-${index}`}>
                        <th>
                          {kickoffLabel(row.saved_at, {
                            year: "numeric",
                            second: "2-digit",
                          })}
                          <small className="observation-source">
                            {row.legacy
                              ? "Original saved forecast"
                              : `Retrieved ${kickoffLabel(row.received_at || row.saved_at)}`}
                          </small>
                        </th>
                        {sides.map((side) => (
                          <td key={side}>
                            {(row.probabilities[side] * 100).toFixed(1)}%
                          </td>
                        ))}
                        <td>{row.model_version || "Unrecorded"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : (
          <div className="fan-empty">
            <h2>A timeline starts with a forecast</h2>
            <p>
              Open an upcoming match forecast. Future visits will add
              observations; past changes cannot be recovered.
            </p>
            <Link className="flood-button" to="/matches">
              Find a match
            </Link>
          </div>
        )}
        <details className="fan-method">
          <summary>What movement can and cannot tell us</summary>
          <p>
            A change describes the recorded probabilities, not its cause. No
            injuries, team news or betting signals are inferred from a change.
            Observations do not alter the tracker’s original snapshot or the
            game’s frozen model pick. Identical observations within one minute
            are deduplicated; storage retains up to 200 observations per fixture
            and 5,000 overall. Clearing site data removes this local record.
          </p>
        </details>
      </section>
    </MainLayout>
  );
}
