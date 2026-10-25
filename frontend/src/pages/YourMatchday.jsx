import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FiRefreshCw } from "react-icons/fi";
import MainLayout from "../components/layout/MainLayout";
import ClubCrest from "../components/ClubCrest";
import CalendarExport from "../components/matches/CalendarExport";
import { getAccountFavourites, getWatchlist } from "../api/accountApi";
import { getTeamProfile } from "../api/teamApi";
import { getMatch } from "../api/matchApi";
import {
  fixtureDate,
  kickoffLabel,
  normaliseFixture,
} from "../utils/fixturePresentation";
import { readForecastArchive } from "../utils/forecastTracker";
import "../styles/fan-features.css";

async function loadLimited(values, loader) {
  const result = [];
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(4, values.length) }, async () => {
      while (next < values.length) {
        const index = next++;
        try {
          result[index] = await loader(values[index]);
        } catch {
          result[index] = null;
        }
      }
    }),
  );
  return result;
}
export default function YourMatchday() {
  const [state, setState] = useState({
    clubs: [],
    matches: [],
    loading: true,
    error: "",
  });
  const [refresh, setRefresh] = useState(0),
    [view, setView] = useState("upcoming"),
    [club, setClub] = useState("");
  const saved = new Map(readForecastArchive().map((row) => [String(row.match_id), row]));
  useEffect(() => {
    let active = true;
    setState((previous) => ({ ...previous, loading: true, error: "" }));
    async function load() {
      const [followed, watchlist] = await Promise.allSettled([
        getAccountFavourites({timeout:12000}),
        getWatchlist({timeout:12000}),
      ]);
      if (followed.status === "rejected" && watchlist.status === "rejected")
        throw new Error(
          "Your saved clubs and fixtures could not be loaded. Please retry.",
        );
      const ids =
        followed.status === "fulfilled"
          ? followed.value
              .filter((row) => row.entity_type === "team")
              .map((row) => row.entity_id)
          : [];
      const profiles = await loadLimited(ids, (id) =>
        getTeamProfile(id, { timeout: 12000 }),
      );
      const watched =
        watchlist.status === "fulfilled"
          ? await loadLimited(watchlist.value, (row) =>
              getMatch(row.match_id, { timeout: 12000 }),
            )
          : [];
      const matches = new Map();
      function add(raw, id, watched = false) {
        const match = normaliseFixture(raw);
        if (!match?.id) return;
        const key = String(match.id),
          old = matches.get(key);
        matches.set(key, {
          ...old,
          ...match,
          watched: watched || old?.watched,
          clubs: [
            ...new Set([...(old?.clubs || []), ...(id ? [String(id)] : [])]),
          ],
        });
      }
      profiles
        .filter(Boolean)
        .forEach((profile) =>
          [
            ...(profile.upcoming_fixtures || []),
            ...(profile.recent_results || []),
          ].forEach((match) => add(match, profile.id)),
        );
      watched.filter(Boolean).forEach((match) => {
        add(match, null, true);
        ids.filter(id => [String(match.home_team_id), String(match.away_team_id)].includes(String(id))).forEach(id => add(match, id, true));
      });
      const missing =
        profiles.some((profile) => !profile) ||
        watched.some((match) => !match) ||
        followed.status === "rejected" ||
        watchlist.status === "rejected";
      if (active)
        setState({
          clubs: profiles.filter(Boolean),
          matches: [...matches.values()],
          loading: false,
          error: missing
            ? "Some club or saved-fixture data could not be loaded. Available matches are shown; refresh to retry."
            : "",
        });
    }
    load().catch(
      (error) =>
        active &&
        setState((previous) => ({
          ...previous,
          loading: false,
          error: error.message,
        })),
    );
    const update = () => setRefresh((value) => value + 1);
    window.addEventListener("football-favourites-updated", update);
    return () => {
      active = false;
      window.removeEventListener("football-favourites-updated", update);
    };
  }, [refresh]);
  const filtered = state.matches.filter(
    (match) => !club || match.clubs.includes(club),
  );
  const upcoming = filtered
    .filter(
      (match) =>
        ["SCHEDULED", "TIMED"].includes(match.status) &&
        fixtureDate(match.utc_date)?.getTime() > Date.now(),
    )
    .sort((a, b) => fixtureDate(a.utc_date) - fixtureDate(b.utc_date));
  const results = filtered
    .filter(
      (match) =>
        match.status === "FINISHED" &&
        fixtureDate(match.utc_date)?.getTime() <= Date.now() &&
        [match.home_score, match.away_score].every(
          (value) => Number.isInteger(value) && value >= 0,
        ),
    )
    .sort((a, b) => fixtureDate(b.utc_date) - fixtureDate(a.utc_date));
  const live = filtered.filter((match) =>
    ["LIVE", "IN_PLAY", "PAUSED"].includes(match.status),
  );
  const visible =
    view === "upcoming" ? upcoming : view === "results" ? results : live;
  return (
    <MainLayout>
      <section className="fan-page">
        <header className="fan-page-heading">
          <div>
            <h1>Your matchday</h1>
            <p>
              The clubs you follow. The fixtures you saved. Your football,
              together.
            </p>
          </div>
          <button
            className="flood-button subtle"
            disabled={state.loading}
            onClick={() => setRefresh((value) => value + 1)}
          >
            <FiRefreshCw /> Refresh feed
          </button>
        </header>
        <div className="personal-clubs">
          {state.clubs.map((team) => (
            <button
              key={team.id}
              aria-pressed={club === String(team.id)}
              onClick={() =>
                setClub(club === String(team.id) ? "" : String(team.id))
              }
            >
              <ClubCrest name={team.name} src={team.crest} />
              <span>{team.name}</span>
            </button>
          ))}
          <Link to="/teams">Manage your clubs</Link>
        </div>
        {state.error && (
          <p role="alert" className="fan-error">
            {state.error}
          </p>
        )}
        <div className="fan-filters">
          <div className="fan-actions">
            {[
              ["upcoming", "Upcoming", upcoming.length],
              ["live", "Live", live.length],
              ["results", "Results", results.length],
            ].map(([value, label, count]) => (
              <button
                className={`flood-button ${view === value ? "" : "subtle"}`}
                aria-pressed={view === value}
                key={value}
                onClick={() => setView(value)}
              >
                {label} ({count})
              </button>
            ))}
          </div>
          <CalendarExport fixtures={upcoming} />
        </div>
        <p className="fan-scope">
          Account favourites and watchlist, using stored club fixture lists and
          up to five recent results per club. Refresh to check for updates.
          Saved forecast previews are local to this browser.
        </p>
        {state.loading ? (
          <div className="fan-empty" role="status">
            Loading your matchday…
          </div>
        ) : visible.length ? (
          <div className="personal-fixtures">
            {visible.map((match) => {
              const snapshot = saved.get(String(match.id));
              return (
                <article key={match.id} className="personal-fixture">
                  <div className="personal-fixture-date">
                    <small>
                      {match.competition_name || "Competition unavailable"}
                      {match.watched ? " · Watchlist" : ""}
                    </small>
                    <span>{kickoffLabel(match.utc_date)}</span>
                  </div>
                  <Link className="personal-pair" to={`/matches/${match.id}`}>
                    <span>
                      <ClubCrest
                        name={match.home_team_name}
                        src={match.home_team_crest}
                      />
                      {match.home_team_name}
                    </span>
                    <strong>
                      {match.status === "FINISHED" ||
                      ["LIVE", "IN_PLAY", "PAUSED"].includes(match.status)
                        ? `${match.home_score ?? "—"}–${match.away_score ?? "—"}`
                        : "vs"}
                    </strong>
                    <span>
                      <ClubCrest
                        name={match.away_team_name}
                        src={match.away_team_crest}
                      />
                      {match.away_team_name}
                    </span>
                  </Link>
                  {snapshot ? (
                    <p>
                      Saved forecast · Home{" "}
                      {(snapshot.probabilities.home * 100).toFixed(1)}% · Draw{" "}
                      {(snapshot.probabilities.draw * 100).toFixed(1)}% · Away{" "}
                      {(snapshot.probabilities.away * 100).toFixed(1)}%
                    </p>
                  ) : (
                    <p>No forecast saved in this browser yet.</p>
                  )}
                  <div className="fan-actions">
                    <Link
                      className="flood-button subtle"
                      to={`/matches/${match.id}`}
                    >
                      {view === "results"
                        ? "Match & saved forecast"
                        : "Open forecast"}
                    </Link>
                    {view === "upcoming" && (
                      <Link
                        className="flood-button"
                        to={`/fan-vs-model?match=${match.id}`}
                      >
                        Make your pick
                      </Link>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="fan-empty">
            <h2>
              {state.clubs.length || state.matches.length
                ? "Nothing in this view yet"
                : "Make matchday yours"}
            </h2>
            <p>
              {state.clubs.length || state.matches.length
                ? "Try another view or club. A missing fixture is not evidence that no match is scheduled."
                : "Follow a club or save a fixture to build your personal feed."}
            </p>
            <Link className="flood-button" to="/teams">
              Find clubs to follow
            </Link>
          </div>
        )}
      </section>
    </MainLayout>
  );
}
