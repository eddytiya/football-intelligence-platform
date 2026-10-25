import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FiDownload, FiRefreshCw } from "react-icons/fi";
import MainLayout from "../components/layout/MainLayout";
import { getMatch } from "../api/matchApi";
import {
  ARCHIVE_KEY,
  readForecastArchive,
  reconcileForecasts,
  scoreForecasts,
} from "../utils/forecastTracker";
import { downloadText } from "../utils/calendarExport";
import { kickoffLabel, fixtureDate } from "../utils/fixturePresentation";
import "../styles/fan-features.css";

const percent = (value) =>
  value == null ? "—" : `${(value * 100).toFixed(1)}%`;
const outcome = (value) =>
  ({ home: "Home win", draw: "Draw", away: "Away win" })[value] || "—";

export default function PredictionTracker() {
  const [rows, setRows] = useState([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [league, setLeague] = useState(""),
    [model, setModel] = useState(""),
    [view, setView] = useState("all");
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = useCallback(() => setRefreshKey((key) => key + 1), []);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const snapshots = readForecastArchive();
    setLoading(true);
    setError("");
    try {
      localStorage.setItem(ARCHIVE_KEY, JSON.stringify(snapshots));
    } catch {
      setError(
        "Browser storage is full or unavailable. Existing forecasts can be read, but new records may not persist.",
      );
    }
    reconcileForecasts(snapshots, (id) => getMatch(id, { signal: controller.signal, timeout: 12000 })).then((data) => {
      if (active) {
        setRows(data);
        setLoading(false);
      }
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [refreshKey]);
  const filtered = useMemo(
    () =>
      rows.filter(
        (row) =>
          (!league || row.league === league) &&
          (!model || (row.model_version || "Unrecorded") === model),
      ),
    [rows, league, model],
  );
  const visible = filtered.filter(
    (row) => view === "all" || row.state === view,
  );
  const metrics = scoreForecasts(filtered);
  const settled = filtered.filter((row) => row.state === "settled");
  const dates = settled
    .map((row) => fixtureDate(row.match.utc_date))
    .sort((a, b) => a - b);
  const leagues = [
    ...new Set(rows.map((row) => row.league).filter(Boolean)),
  ].sort();
  const models = [
    ...new Set(rows.map((row) => row.model_version || "Unrecorded")),
  ].sort();
  const byLeague = [
    ...new Set(filtered.map((row) => row.league).filter(Boolean)),
  ].map((name) => ({
    name,
    ...scoreForecasts(filtered.filter((row) => row.league === name)),
  }));
  const exportResults = () => {
    const cell = (value) =>
      `"${String(value ?? "")
        .replace(/^[=+@-]/, "'$&")
        .replaceAll('"', '""')}"`;
    const lines = [
      [
        "Match ID",
        "Home",
        "Away",
        "League",
        "Saved UTC",
        "Kickoff UTC",
        "Model",
        "Home probability",
        "Draw probability",
        "Away probability",
        "State",
        "Actual",
        "Top pick",
        "Log loss",
      ],
      ...filtered.map((row) => [
        row.match_id,
        row.home_team,
        row.away_team,
        row.league,
        row.saved_at,
        row.match?.utc_date || row.utc_date,
        row.model_version,
        row.probabilities.home,
        row.probabilities.draw,
        row.probabilities.away,
        row.state,
        row.actual,
        row.picked,
        row.loss,
      ]),
    ];
    downloadText(
      lines.map((line) => line.map(cell).join(",")).join("\r\n"),
      "prediction-tracker.csv",
      "text/csv;charset=utf-8",
    );
  };
  return (
    <MainLayout>
      <section className="fan-page tracker-page">
        <header className="fan-page-heading">
          <div>
            <h1>Prediction tracker</h1>
            <p>What we forecast. What actually happened.</p>
          </div>
          <div className="fan-actions">
            <button
              className="flood-button subtle"
              onClick={refresh}
              disabled={loading}
            >
              <FiRefreshCw />{" "}
              {loading ? "Checking results…" : "Refresh results"}
            </button>
            <button
              className="flood-button subtle"
              onClick={exportResults}
              disabled={loading || !filtered.length}
            >
              <FiDownload /> Export CSV
            </button>
          </div>
        </header>
        <p className="fan-scope">
          Your browser’s saved pre-match forecasts, checked against stored final
          results. This is a personal sample, not a complete evaluation of the
          live model. Records are local to this browser and are not
          account-synced.
        </p>
        {error && (
          <p role="alert" className="fan-error">
            {error}
          </p>
        )}
        <div className="fan-filters">
          <label>
            Competition
            <select
              aria-label="Competition"
              value={league}
              onChange={(event) => setLeague(event.target.value)}
            >
              <option value="">All competitions</option>
              {leagues.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
          </label>
          <label>
            Model version
            <select
              aria-label="Model version"
              value={model}
              onChange={(event) => setModel(event.target.value)}
            >
              <option value="">All saved versions</option>
              {models.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
          </label>
          <label>
            Records
            <select
              aria-label="Records"
              value={view}
              onChange={(event) => setView(event.target.value)}
            >
              <option value="all">All saved forecasts</option>
              <option value="settled">Completed & scored</option>
              <option value="pending">Awaiting result</option>
              <option value="unavailable">Result unavailable</option>
              <option value="excluded">Excluded from scoring</option>
            </select>
          </label>
        </div>
        {loading ? (
          <div className="fan-empty" role="status">
            Checking saved forecasts and results…
          </div>
        ) : (
          <>
            <section
              className="tracker-scoreboard"
              aria-label="Forecast performance"
            >
              <div>
                <span>Top-pick accuracy</span>
                <strong>{percent(metrics.accuracy)}</strong>
                <small>
                  {metrics.correct} correct / {metrics.count} scored
                </small>
              </div>
              <div>
                <span>Log loss</span>
                <strong>
                  {metrics.logLoss == null ? "—" : metrics.logLoss.toFixed(3)}
                </strong>
                <small>Lower is better · natural logarithm</small>
              </div>
              <div>
                <span>Draw recall</span>
                <strong>{percent(metrics.drawRecall)}</strong>
                <small>
                  {metrics.correctDraws} found / {metrics.actualDraws} actual
                  draws
                </small>
              </div>
              <div>
                <span>Draw precision</span>
                <strong>{percent(metrics.drawPrecision)}</strong>
                <small>
                  {metrics.correctDraws} correct / {metrics.selectedDraws} draw
                  picks
                </small>
              </div>
            </section>
            <p className="fan-scope">
              {dates.length
                ? `Scored kickoff period: ${dates[0].toLocaleDateString()}–${dates.at(-1).toLocaleDateString()}.`
                : "No eligible completed forecasts yet."}{" "}
              {filtered.filter((row) => row.state === "pending").length}{" "}
              awaiting results ·{" "}
              {filtered.filter((row) => row.state === "unavailable").length}{" "}
              could not be checked ·{" "}
              {filtered.filter((row) => row.state === "excluded").length}{" "}
              excluded.{" "}
              {metrics.count > 0 &&
                metrics.count < 100 &&
                "Small sample: these figures can change sharply after a few matches."}
            </p>
            <section className="fan-section">
              <h2>Results by league</h2>
              <div className="fan-table-scroll">
                <table className="fan-table">
                  <thead>
                    <tr>
                      <th>Competition</th>
                      <th>Scored</th>
                      <th>Accuracy</th>
                      <th>Log loss</th>
                      <th>Draws found</th>
                    </tr>
                  </thead>
                  <tbody>
                    {byLeague.length ? (
                      byLeague.map((item) => (
                        <tr key={item.name}>
                          <th>{item.name}</th>
                          <td>{item.count}</td>
                          <td>{percent(item.accuracy)}</td>
                          <td>
                            {item.logLoss == null
                              ? "—"
                              : item.logLoss.toFixed(3)}
                          </td>
                          <td>
                            {item.correctDraws} / {item.actualDraws}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5">
                          League results will appear as your saved forecasts are
                          checked.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="fan-section">
              <h2>Forecasts & final results</h2>
              {visible.length ? (
                <div className="tracker-records">
                  {visible.map((row) => (
                    <article key={row.match_id} className="tracker-record">
                      <div>
                        <Link to={`/matches/${row.match_id}`}>
                          {row.home_team} <span>vs</span> {row.away_team}
                        </Link>
                        <small>
                          {kickoffLabel(row.match?.utc_date || row.utc_date)} ·{" "}
                          {row.league || "Competition unavailable"}
                        </small>
                        <small>
                          Saved {kickoffLabel(row.saved_at)} ·{" "}
                          {row.model_version || "Model version unrecorded"}
                        </small>
                      </div>
                      <div className="tracker-record-outcome">
                        <span>
                          H {percent(row.probabilities.home)} · D{" "}
                          {percent(row.probabilities.draw)} · A{" "}
                          {percent(row.probabilities.away)}
                        </span>
                        {row.state === "settled" ? (
                          <>
                            <strong>
                              {row.match.home_score}–{row.match.away_score} ·{" "}
                              {row.correct ? "Correct pick" : "Missed pick"}
                            </strong>
                            <small>
                              {outcome(row.picked)} · log loss{" "}
                              {row.loss.toFixed(3)}
                              {row.tied ? " · tied top probability" : ""}
                            </small>
                          </>
                        ) : (
                          <strong>{row.reason}</strong>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="fan-empty">
                  <h3>
                    {rows.length
                      ? "No forecasts match these filters"
                      : "Your record starts before kickoff"}
                  </h3>
                  <p>
                    {rows.length
                      ? "Choose a different competition, model or record status."
                      : "Open an upcoming match’s forecast to save it automatically. Return after full time to see the result here. Older incomplete or post-kickoff records are not scored."}
                  </p>
                  <Link className="flood-button" to="/matches">
                    Find a match
                  </Link>
                </div>
              )}
            </section>
          </>
        )}
        <details className="fan-method">
          <summary>How scoring works</summary>
          <p>
            Each fixture counts once, using its earliest valid saved snapshot.
            The saved time must precede both its recorded kickoff and the
            current fixture kickoff. Only FINISHED matches with a past kickoff
            and valid full-time scores count. Postponed, cancelled and
            unverified results are not scored.
          </p>
          <p>
            Top pick means the largest of home, draw and away probabilities,
            even when below 50%. Exact ties use home, then draw, then away. Log
            loss is the mean of −ln(probability assigned to the actual result),
            clipped at 10⁻¹⁵ for zero probabilities. Uniform three-way
            probabilities give approximately 1.099. Draw recall measures actual
            draws found; draw precision measures how often a draw pick was
            correct. Neither is overall accuracy.
          </p>
          <p>
            Browser records are not tamper-proof or independently audited.
            Clearing site data removes them. The recent-history Clear button
            does not clear this tracker archive. Export CSV to keep a copy.
          </p>
        </details>
      </section>
    </MainLayout>
  );
}
