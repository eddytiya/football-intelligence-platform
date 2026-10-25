import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import MatchCard from "../components/matches/MatchCard";
import {
  getMatch,
  getUpcomingMatches,
  searchMatchesByTeam,
} from "../api/matchApi";
import { getTeams } from "../api/teamApi";
import "./Predictions.css";

function Predictions() {
  const navigate = useNavigate();
  const [fixtures, setFixtures] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [search, setSearch] = useState("");
  const [teams, setTeams] = useState([]);
  const [favouriteTeam, setFavouriteTeam] = useState(
    () => localStorage.getItem("prediction-favourite-team") || "",
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [savedClubIds, setSavedClubIds] = useState(() =>
    JSON.parse(localStorage.getItem("football-team-favourites") || "[]"),
  );

  const refreshPredictionHistory = async () => {
    let stored = [];
    try {
      stored = JSON.parse(localStorage.getItem("prediction-history") || "[]");
    } catch {
      stored = [];
    }
    const enriched = await Promise.all(
      stored.slice(0, 8).map(async (item) => {
        try {
          const latest = await getMatch(item.match_id);
          return {
            ...item,
            status: latest.status,
            finalScore:
              latest.status === "FINISHED"
                ? `${latest.home_score}–${latest.away_score}`
                : null,
          };
        } catch {
          return item;
        }
      }),
    );
    setPredictionHistory(enriched);
  };

  useEffect(() => {
    getUpcomingMatches(30)
      .then((data) => {
        setFixtures(data);
      })
      .catch(() => setError("Upcoming fixtures are unavailable right now."))
      .finally(() => setLoading(false));
    getTeams({ limit: 500 })
      .then(setTeams)
      .catch(() => setTeams([]));
  }, []);

  useEffect(() => {
    refreshPredictionHistory();
  }, []);

  useEffect(() => {
    const refreshSavedClubs = () =>
      setSavedClubIds(
        JSON.parse(localStorage.getItem("football-team-favourites") || "[]"),
      );
    window.addEventListener("football-favourites-updated", refreshSavedClubs);
    return () =>
      window.removeEventListener(
        "football-favourites-updated",
        refreshSavedClubs,
      );
  }, []);

  useEffect(() => {
    const term = search.trim();
    if (!term) return undefined;
    let active = true;
    const timer = setTimeout(() => {
      searchMatchesByTeam(term)
        .then((data) => active && setFixtures(data))
        .catch(() => active && setFixtures([]));
    }, 250);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [search]);

  useEffect(() => {
    if (!favouriteTeam) {
      localStorage.removeItem("prediction-favourite-team");
      return;
    }
    localStorage.setItem("prediction-favourite-team", favouriteTeam);
    setSearch(favouriteTeam);
  }, [favouriteTeam]);

  const visibleFixtures = useMemo(
    () =>
      fixtures
        .filter((match) => ["SCHEDULED", "TIMED"].includes(match.status))
        .slice(0, 12),
    [fixtures],
  );
  const savedClubs = useMemo(
    () => teams.filter((team) => savedClubIds.includes(team.id)),
    [teams, savedClubIds],
  );
  const chooseFixture = (match) => navigate(`/matches/${match.id}`);
  const chooseFavouriteTeam = (teamName) => {
    setFavouriteTeam(teamName);
    setSelectedMatch(null);
  };

  if (loading)
    return (
      <MainLayout>
        <FootballLoader label="Loading prediction fixtures" />
      </MainLayout>
    );

  return (
    <MainLayout>
      <section className="prediction-centre-page">
        <header className="prediction-centre-hero">
          <div>
            <span>Match intelligence</span>
            <h1>Prediction Centre</h1>
            <Link className="flood-button subtle" to="/prediction-tracker">View prediction tracker</Link>
            <Link className="flood-button subtle" to="/confidence-explorer">Confidence explorer</Link>
            <Link className="flood-button subtle" to="/forecast-movement">Forecast movement</Link>
            <p>
              Choose an upcoming fixture to see the model’s probability, likely
              scoreline, form, data coverage and match reasoning.
            </p>
            <div className="prediction-hero-pills">
              <b>Expected goals</b>
              <b>Form & momentum</b>
              <b>Transparent reasoning</b>
            </div>
          </div>
          <aside>
            <span>MODEL STATUS</span>
            <strong>READY</strong>
            <small>Historical ML · live fixture data</small>
          </aside>
        </header>

        <section className="prediction-favourite-team">
          <div>
            <span>Your club</span>
            <h2>Start with a favourite team</h2>
            <p>
              Choose a club once. Its scheduled fixtures become your prediction
              list, and your choice is remembered on this browser.
            </p>
            {savedClubs.length > 0 && (
              <div className="prediction-saved-clubs">
                {savedClubs.map((team) => (
                  <button
                    type="button"
                    key={team.id}
                    onClick={() => chooseFavouriteTeam(team.name)}
                  >
                    {team.crest && <img src={team.crest} alt="" />}
                    {team.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <label>
            <span>Favourite team</span>
            <select
              value={favouriteTeam}
              onChange={(event) => chooseFavouriteTeam(event.target.value)}
            >
              <option value="">Choose a team</option>
              {teams.map((team) => (
                <option key={team.id} value={team.name}>
                  {team.name}
                  {team.competition_name ? ` · ${team.competition_name}` : ""}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className="prediction-fixture-picker">
          <header>
            <div>
              <span>Fixture finder</span>
              <h2>
                {favouriteTeam
                  ? `${favouriteTeam} fixtures`
                  : "Choose a club or search a fixture"}
              </h2>
            </div>
            <Link
              to={`/matches?team=${encodeURIComponent(search.trim().length >= 2 ? search.trim() : favouriteTeam)}`}
            >
              {search.trim().length >= 2
                ? `Open ${search.trim()} fixtures →`
                : "Open matches →"}
            </Link>
          </header>
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              if (event.target.value !== favouriteTeam) setFavouriteTeam("");
            }}
            placeholder="Search a team, e.g. Barcelona or Arsenal…"
          />
          {loading ? (
            <p>Loading upcoming fixtures…</p>
          ) : error ? (
            <p className="prediction-page-error">{error}</p>
          ) : (
            <div className="prediction-fixture-list">
              {visibleFixtures.map((match) => (
                <button
                  type="button"
                  className={
                    selectedMatch?.id === match.id ? "is-selected" : ""
                  }
                  key={match.id}
                  onClick={() => chooseFixture(match)}
                >
                  <span>
                    {new Date(match.utc_date).toLocaleDateString(undefined, {
                      day: "numeric",
                      month: "short",
                    })}{" "}
                    ·{" "}
                    {new Date(match.utc_date).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <strong>
                    {match.home_team_name} <i>vs</i> {match.away_team_name}
                  </strong>
                  <small>
                    {match.competition_name}
                    {match.match_week ? ` · MW ${match.match_week}` : ""}
                  </small>
                </button>
              ))}
            </div>
          )}
        </section>

        {selectedMatch ? (
          <section className="prediction-analysis">
            <header>
              <div>
                <span>Selected fixture</span>
                <h2>
                  {selectedMatch.home_team_name} <i>vs</i>{" "}
                  {selectedMatch.away_team_name}
                </h2>
                <p>
                  {selectedMatch.competition_name} ·{" "}
                  {new Date(selectedMatch.utc_date).toLocaleString(undefined, {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <div className="prediction-disclaimer">
                <b>MODEL ESTIMATE</b>
                <small>
                  Football remains unpredictable. This is an evidence-led
                  forecast, not a guarantee.
                </small>
              </div>
            </header>
            <div className="prediction-team-fixture-links">
              <span>Explore the full scheduled season</span>
              <Link
                to={`/matches?team=${encodeURIComponent(selectedMatch.home_team_name)}`}
              >
                {selectedMatch.home_team_name} fixtures →
              </Link>
              <Link
                to={`/matches?team=${encodeURIComponent(selectedMatch.away_team_name)}`}
              >
                {selectedMatch.away_team_name} fixtures →
              </Link>
            </div>
            <MatchCard
              match={selectedMatch}
              autoShowPrediction
              onPredictionSaved={refreshPredictionHistory}
            />
          </section>
        ) : (
          !loading && (
            <div className="prediction-empty">
              Search for a scheduled fixture to begin analysis.
            </div>
          )
        )}

        <section className="prediction-history">
          <header>
            <div>
              <span>Prediction history</span>
              <h2>Forecasts saved before kick-off</h2>
            </div>
            {predictionHistory.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem("prediction-history");
                  setPredictionHistory([]);
                }}
              >
                Clear saved forecasts
              </button>
            )}
          </header>
          {predictionHistory.length ? (
            <div>
              {predictionHistory.map((item) => (
                <article key={item.match_id}>
                  <div>
                    <small>
                      {new Date(item.utc_date).toLocaleDateString(undefined, {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </small>
                    <strong>
                      {item.home_team} <i>vs</i> {item.away_team}
                    </strong>
                  </div>
                  <div>
                    <span>
                      Forecast: {item.predicted_outcome}
                      {item.likely_score ? ` · ${item.likely_score}` : ""}
                    </span>
                    <b>
                      {item.finalScore
                        ? `Final: ${item.finalScore}`
                        : item.status === "LIVE"
                          ? "Live now"
                          : "Forecast saved"}
                    </b>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p>
              Open a fixture prediction to save it here. Completed fixtures will
              show their real final score when live data updates.
            </p>
          )}
        </section>

        <section className="prediction-method">
          <article>
            <span>Result probabilities</span>
            <p>
              Shows the chance of each club winning or drawing, plus confidence
              based on separation and data coverage.
            </p>
          </article>
          <article>
            <span>Score projection</span>
            <p>
              Uses expected goals to produce a most-likely scoreline and
              alternative likely scores.
            </p>
          </article>
          <article>
            <span>Why the model leans</span>
            <p>
              Explains the impact of form, attack, defence, rest days, home
              advantage and head-to-head data.
            </p>
          </article>
        </section>
      </section>
    </MainLayout>
  );
}

export default Predictions;
