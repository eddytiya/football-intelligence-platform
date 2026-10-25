import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FiRepeat } from "react-icons/fi";
import MainLayout from "../components/layout/MainLayout";
import ClubCrest from "../components/ClubCrest";
import CalendarExport from "../components/matches/CalendarExport";
import OutcomeProbabilities from "../components/predictions/OutcomeProbabilities";
import { getTeams, getTeamProfile, getTeamComparison } from "../api/teamApi";
import {
  fixtureDate,
  kickoffLabel,
  normaliseFixture,
} from "../utils/fixturePresentation";
import useFixtureForecast from "../hooks/useFixtureForecast";
import "../styles/fan-features.css";

function MeetingForecast({ match }) {
  const { forecast, loading, error } = useFixtureForecast(match);
  return (
    <section className="fan-section">
      <h2>The next meeting</h2>
      <p>
        <Link to={`/matches/${match.id}`}>
          {match.home_team_name} vs {match.away_team_name}
        </Link>{" "}
        · {kickoffLabel(match.utc_date)}
      </p>
      {loading ? (
        <p role="status">Loading the match forecast…</p>
      ) : forecast ? (
        <OutcomeProbabilities
          forecast={forecast}
          home={match.home_team_name}
          away={match.away_team_name}
        />
      ) : (
        <p>{error || "Forecast unavailable for this meeting."}</p>
      )}
      <CalendarExport fixtures={[match]} />
    </section>
  );
}

export default function ClubComparison() {
  const [params, setParams] = useSearchParams();
  const first = params.get("first") || "",
    second = params.get("second") || "";
  const [query, setQuery] = useState(""),
    [teams, setTeams] = useState([]),
    [directoryError, setDirectoryError] = useState("");
  const [data, setData] = useState(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      setDirectoryError("");
      getTeams({ query, limit: 100 })
        .then((rows) => active && setTeams(rows))
        .catch(
          () =>
            active &&
            setDirectoryError(
              "Club search is unavailable. Try searching again.",
            ),
        );
    }, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query]);
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    if (!first || !second || first === second) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      getTeamProfile(first),
      getTeamProfile(second),
      getTeamComparison(first, second),
    ])
      .then(
        ([home, away, meetings]) =>
          active &&
          setData({
            home: {
              ...home,
              recent_results: (home.recent_results || []).map(normaliseFixture),
              upcoming_fixtures: (home.upcoming_fixtures || []).map(
                normaliseFixture,
              ),
            },
            away: {
              ...away,
              recent_results: (away.recent_results || []).map(normaliseFixture),
              upcoming_fixtures: (away.upcoming_fixtures || []).map(
                normaliseFixture,
              ),
            },
            meetings: {
              ...meetings,
              recent_meetings: (meetings.recent_meetings || []).map(
                normaliseFixture,
              ),
            },
          }),
      )
      .catch(
        () =>
          active &&
          setError("This comparison could not be loaded. Please try again."),
      )
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [first, second, retry]);
  const choose = (side, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(side, value);
    else next.delete(side);
    setParams(next);
  };
  const options = (id, profile) => {
    const rows = [...teams];
    if (id && !rows.some((team) => String(team.id) === id))
      rows.unshift(profile || { id, name: `Selected club #${id}` });
    return rows;
  };
  const upcoming = data
    ? [...data.home.upcoming_fixtures, ...data.away.upcoming_fixtures].find(
        (match) =>
          fixtureDate(match.utc_date)?.getTime() > Date.now() &&
          ["SCHEDULED", "TIMED"].includes(match.status) &&
          [match.home_team_name, match.away_team_name].includes(
            data.home.name,
          ) &&
          [match.home_team_name, match.away_team_name].includes(data.away.name),
      )
    : null;
  const stat = (team, key) =>
    team.recent_results?.length ? (team.form_summary?.[key] ?? "—") : "—";
  return (
    <MainLayout>
      <section className="fan-page comparison-page">
        <header className="fan-page-heading">
          <div>
            <h1>Club comparison</h1>
            <p>Two clubs. The form, the goals, the history.</p>
          </div>
        </header>
        <div className="fan-filters comparison-picker">
          <label>
            Find clubs
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search the club directory"
            />
          </label>
          <label>
            First club
            <select
              value={first}
              onChange={(event) => choose("first", event.target.value)}
            >
              <option value="">Choose a club</option>
              {options(first, data?.home).map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="flood-button subtle"
            aria-label="Swap clubs"
            disabled={!first || !second}
            onClick={() => setParams({ first: second, second: first })}
          >
            <FiRepeat />
          </button>
          <label>
            Second club
            <select
              value={second}
              onChange={(event) => choose("second", event.target.value)}
            >
              <option value="">Choose a club</option>
              {options(second, data?.away).map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {directoryError && <p role="alert">{directoryError}</p>}
        {first && second && first === second && (
          <p role="alert">Choose two different clubs to compare.</p>
        )}
        {loading && (
          <div className="fan-empty" role="status">
            Loading club form and meetings…
          </div>
        )}
        {error && (
          <div className="fan-empty" role="alert">
            <p>{error}</p>
            <button
              className="flood-button"
              onClick={() => setRetry((value) => value + 1)}
            >
              Try again
            </button>
          </div>
        )}
        {data ? (
          <>
            <div className="comparison-clubs">
              {[data.home, data.away].map((team) => (
                <Link to={`/teams/${team.id}`} key={team.id}>
                  <ClubCrest name={team.name} src={team.crest} />
                  <h2>{team.name}</h2>
                  <span>{team.venue || "Venue not supplied"}</span>
                  <div
                    className="comparison-form"
                    aria-label="Recent form, latest first"
                  >
                    {team.form?.length
                      ? team.form.map((result, index) => (
                          <span
                            className={`form-${result.toLowerCase()}`}
                            key={index}
                          >
                            {result}
                          </span>
                        ))
                      : "No recent form recorded"}
                  </div>
                </Link>
              ))}
            </div>
            <section className="fan-section">
              <h2>Recent form, side by side</h2>
              <p>
                Up to five stored completed matches per club, latest first.
                Samples may cover different dates and competitions.
              </p>
              <div className="fan-table-scroll">
                <table className="fan-table comparison-table">
                  <thead>
                    <tr>
                      <th>{data.home.name}</th>
                      <th>Measure</th>
                      <th>{data.away.name}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{data.home.recent_results.length}</td>
                      <th>Matches in sample</th>
                      <td>{data.away.recent_results.length}</td>
                    </tr>
                    {[
                      ["wins", "Wins"],
                      ["draws", "Draws"],
                      ["losses", "Losses"],
                      ["goals_for", "Goals scored"],
                      ["goals_against", "Goals conceded"],
                    ].map(([key, title]) => (
                      <tr key={key}>
                        <td>{stat(data.home, key)}</td>
                        <th>{title}</th>
                        <td>{stat(data.away, key)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="fan-section">
              <h2>Head-to-head</h2>
              <p>
                {data.meetings.meetings} stored meetings ·{" "}
                {data.meetings.period || "Available history"}. Historical
                meetings are context, not a prediction.
              </p>
              {data.meetings.meetings ? (
                <>
                  <div className="comparison-h2h">
                    <span>
                      <b>{data.meetings.first_team_wins}</b>
                      {data.home.name} wins
                    </span>
                    <span>
                      <b>{data.meetings.draws}</b>Draws
                    </span>
                    <span>
                      <b>{data.meetings.second_team_wins}</b>
                      {data.away.name} wins
                    </span>
                  </div>
                  <div className="comparison-results">
                    {data.meetings.recent_meetings.map((match) => (
                      <Link to={`/matches/${match.id}`} key={match.id}>
                        <small>{kickoffLabel(match.utc_date)}</small>
                        <span>{match.home_team_name}</span>
                        <strong>
                          {match.home_score}–{match.away_score}
                        </strong>
                        <span>{match.away_team_name}</span>
                      </Link>
                    ))}
                  </div>
                </>
              ) : (
                <p>No completed meetings are available in this dataset.</p>
              )}
            </section>
            {upcoming ? (
              <MeetingForecast match={upcoming} />
            ) : (
              <section className="fan-section">
                <h2>Next meeting</h2>
                <p>
                  No verified upcoming meeting was found in these clubs’ stored
                  fixture lists. We won’t invent probabilities for an
                  unscheduled pairing.
                </p>
                <Link to="/matches">Browse fixtures</Link>
              </section>
            )}
            <div className="comparison-recent">
              {[data.home, data.away].map((team) => (
                <section className="fan-section" key={team.id}>
                  <h2>{team.name} results</h2>
                  {team.recent_results.length ? (
                    team.recent_results.map((match) => (
                      <p key={match.id}>
                        <small>{kickoffLabel(match.utc_date)}</small>
                        <br />
                        <Link to={`/matches/${match.id}`}>
                          {match.home_team_name}{" "}
                          <b>
                            {match.home_score}–{match.away_score}
                          </b>{" "}
                          {match.away_team_name}
                        </Link>
                      </p>
                    ))
                  ) : (
                    <p>No completed results recorded.</p>
                  )}
                </section>
              ))}
            </div>
          </>
        ) : (
          !loading &&
          !error && (
            <div className="fan-empty">
              <h2>Pick your two clubs</h2>
              <p>
                Search the directory, then choose both clubs to see their stored
                form and head-to-head record.
              </p>
            </div>
          )
        )}
      </section>
    </MainLayout>
  );
}
