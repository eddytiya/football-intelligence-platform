import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import { getMatch, getUpcomingMatches } from "../api/matchApi";
import { getFanPicks, submitFanPick } from "../api/fanGameApi";
import { fixtureDate, kickoffLabel } from "../utils/fixturePresentation";
import { gameSummary } from "../utils/forecastEvidence";
import "../styles/fan-features.css";

const label = (value) =>
  ({ home: "Home win", draw: "Draw", away: "Away win" })[value] || "—";
const accuracy = (count, total) =>
  total ? `${((100 * count) / total).toFixed(1)}%` : "—";
export default function FanVsModel() {
  const [params] = useSearchParams(),
    selected = params.get("match");
  const [fixtures, setFixtures] = useState([]),
    [picks, setPicks] = useState([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [choice, setChoice] = useState({}),
    [saving, setSaving] = useState(null),
    [query, setQuery] = useState(""),
    [refresh, setRefresh] = useState(0),
    [now, setNow] = useState(Date.now());
  const [displayCount, setDisplayCount] = useState(12);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    Promise.all([
      getUpcomingMatches(80),
      getFanPicks(),
      selected
        ? getMatch(selected, { timeout: 12000 }).catch(() => null)
        : Promise.resolve(null),
    ])
      .then(([upcoming, stored, match]) => {
        if (!active) return;
        setFixtures([
          ...new Map(
            [...(match ? [match] : []), ...upcoming].map((row) => [
              String(row.id),
              row,
            ]),
          ).values(),
        ]);
        setPicks(stored);
      })
      .catch(
        () =>
          active &&
          setError(
            "The game could not be loaded. Check your sign-in and retry.",
          ),
      )
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [selected, refresh]);
  const summary = gameSummary(picks),
    byId = useMemo(
      () => new Map(picks.map((pick) => [String(pick.match_id), pick])),
      [picks],
    );
  const submit = async (match) => {
    if (!choice[match.id]) return;
    setSaving(match.id);
    setError("");
    try {
      const row = await submitFanPick(match.id, choice[match.id]);
      setPicks((previous) => [
        row,
        ...previous.filter(
          (pick) => String(pick.match_id) !== String(row.match_id),
        ),
      ]);
    } catch (failure) {
      setError(
        failure.response?.data?.detail ||
          "The pick could not be confirmed. Refresh your picks before retrying; your request may have reached the server.",
      );
    } finally {
      setSaving(null);
    }
  };
  const eligible = fixtures.filter(
    (match) =>
      ["SCHEDULED", "TIMED"].includes(match.status) &&
      fixtureDate(match.utc_date)?.getTime() > now,
  );
  const visible = eligible.filter((match) =>
    `${match.home_team_name} ${match.away_team_name}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <MainLayout>
      <section className="fan-page">
        <header className="fan-page-heading">
          <div>
            <h1>Fan vs model</h1>
            <p>Back your football knowledge. See how your picks compare.</p>
          </div>
          <button
            className="flood-button subtle"
            disabled={loading || saving !== null}
            onClick={() => setRefresh((value) => value + 1)}
          >
            Refresh picks & results
          </button>
        </header>
        <p className="fan-scope">
          One final home/draw/away pick per fixture, saved to your account.
          Submission is checked on the server before kickoff and cannot be
          edited. The model snapshot is frozen at submission; unavailable model
          forecasts do not enter the head-to-head comparison.
        </p>
        <section
          className="tracker-scoreboard game-scoreboard"
          aria-label="Your game record"
        >
          <div>
            <span>Your accuracy · all completed picks</span>
            <strong>{accuracy(summary.correct, summary.total)}</strong>
            <small>
              {summary.correct} / {summary.total} correct
            </small>
          </div>
          <div>
            <span>You · paired fixtures</span>
            <strong>
              {accuracy(summary.pairedFanCorrect, summary.paired)}
            </strong>
            <small>
              {summary.pairedFanCorrect} / {summary.paired} correct
            </small>
          </div>
          <div>
            <span>Model · same paired fixtures</span>
            <strong>
              {accuracy(summary.pairedModelCorrect, summary.paired)}
            </strong>
            <small>
              {summary.pairedModelCorrect} / {summary.paired} correct
            </small>
          </div>
        </section>
        {summary.paired > 0 && summary.paired < 100 && (
          <p className="fan-scope">
            Small sample: this personal game is not a complete model evaluation.
          </p>
        )}
        {error && (
          <p className="fan-error" role="alert">
            {error}
          </p>
        )}
        <section className="fan-section">
          <h2>Make your next pick</h2>
          <div className="fan-filters">
            <label>
              Find a fixture
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search displayed clubs"
              />
            </label>
            <Link to="/matches">Find more fixtures</Link>
          </div>
          {loading ? (
            <p role="status">Loading the game…</p>
          ) : visible.length ? (
            <div className="game-fixtures">
              {visible.slice(0, displayCount).map((match) => {
                const saved = byId.get(String(match.id));
                return (
                  <article className="game-fixture" key={match.id}>
                    <header>
                      <Link to={`/matches/${match.id}`}>
                        <h3>
                          {match.home_team_name} <span>vs</span>{" "}
                          {match.away_team_name}
                        </h3>
                      </Link>
                      <small>
                        {kickoffLabel(match.utc_date)} ·{" "}
                        {match.competition_name}
                      </small>
                    </header>
                    {saved ? (
                      <p className="game-locked" role="status">
                        Your locked pick: <b>{label(saved.outcome)}</b> ·{" "}
                        {saved.model_probabilities
                          ? "Model snapshot saved"
                          : "Model forecast unavailable"}
                      </p>
                    ) : (
                      <>
                        <fieldset disabled={saving !== null}>
                          <legend>Choose your outcome</legend>
                          <div className="game-choices">
                            {["home", "draw", "away"].map((outcome) => (
                              <label key={outcome}>
                                <input
                                  type="radio"
                                  name={`pick-${match.id}`}
                                  value={outcome}
                                  checked={choice[match.id] === outcome}
                                  onChange={() =>
                                    setChoice((previous) => ({
                                      ...previous,
                                      [match.id]: outcome,
                                    }))
                                  }
                                />
                                <span>{label(outcome)}</span>
                              </label>
                            ))}
                          </div>
                        </fieldset>
                        <button
                          className="flood-button"
                          disabled={!choice[match.id] || saving !== null}
                          onClick={() => submit(match)}
                        >
                          {saving === match.id
                            ? "Saving pick & model snapshot…"
                            : "Lock my pick"}
                        </button>
                      </>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="fan-empty">
              No verified upcoming fixtures match this view. Try Matches for a
              different fixture.
            </div>
          )}
          {visible.length > displayCount && (
            <button
              className="flood-button subtle"
              onClick={() => setDisplayCount((count) => count + 12)}
            >
              Show more fixtures
            </button>
          )}
        </section>
        <section className="fan-section">
          <h2>Your picks & results</h2>
          {picks.length ? (
            <div>
              {picks.map((pick) => (
                <article className="tracker-record" key={pick.match_id}>
                  <div>
                    <Link to={`/matches/${pick.match_id}`}>
                      {pick.home_team_name} vs {pick.away_team_name}
                    </Link>
                    <small>
                      {kickoffLabel(pick.utc_date)} · submitted{" "}
                      {kickoffLabel(pick.saved_at)}
                    </small>
                    <span>You: {label(pick.outcome)}</span>
                  </div>
                  <div className="tracker-record-outcome">
                    {pick.state === "settled" ? (
                      <>
                        <strong>
                          {pick.home_score}–{pick.away_score} ·{" "}
                          {pick.fan_correct ? "You got it" : "Missed pick"}
                        </strong>
                        <span>
                          Model:{" "}
                          {pick.model_pick
                            ? `${label(pick.model_pick)} · ${pick.model_correct ? "correct" : "missed"}`
                            : "No snapshot available"}
                        </span>
                      </>
                    ) : (
                      <strong>
                        {pick.state === "excluded"
                          ? "Excluded from scoring · fixture data/status changed"
                          : "Awaiting verified final result"}
                      </strong>
                    )}
                    <small>
                      {pick.model_version || "Model version unavailable"}
                    </small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p>No picks yet. Choose an upcoming fixture above.</p>
          )}
        </section>
        <details className="fan-method">
          <summary>Game rules & fair comparisons</summary>
          <p>
            Picks are final once submitted. A point is one correct three-way
            outcome; there are no stakes or prizes. Only verified FINISHED
            fixtures with valid scores, unchanged club identities and
            pre-kickoff submission times count. Paired accuracy uses exactly the
            same completed fixtures for you and the model. The model top pick
            uses home/draw/away tie order. Cancelled, awarded, quarantined and
            postponed records are excluded while in that state.
          </p>
        </details>
      </section>
    </MainLayout>
  );
}
