import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FiArrowUpRight, FiSearch, FiStar } from "react-icons/fi";
import { getDashboardCommandCentre } from "../../api/dashboardApi";
import { getAccountFavourites } from "../../api/accountApi";
import { getTeamProfile } from "../../api/teamApi";
import { getCompetitions } from "../../api/competitionApi";
import {
  getCompetitionStandings,
  getLatestMatchDate,
  getMatchesByDate,
} from "../../api/matchApi";
import ClubCrest from "../ClubCrest";
import BroadcastMatchup from "../matches/BroadcastMatchup";
import OutcomeProbabilities from "../predictions/OutcomeProbabilities";
import useFixtureForecast from "../../hooks/useFixtureForecast";
import {
  fixtureDate,
  kickoffLabel,
  normaliseFixture,
} from "../../utils/fixturePresentation";
import FootballLoader from "../layout/FootballLoader";

function FixtureRow({ fixture }) {
  const match = normaliseFixture(fixture);
  const scored = ["FINISHED", "AWARDED", "LIVE", "IN_PLAY", "PAUSED"].includes(
    match.status,
  );
  return (
    <Link className="flood-fixture-row" to={`/matches/${match.id}`}>
      <time>{kickoffLabel(match.utc_date, { weekday: undefined })}</time>
      <div className="flood-fixture-clubs">
        <span>
          <ClubCrest src={match.home_team_crest} name={match.home_team_name} />
          {match.home_team_name}
        </span>
        <b>
          {scored
            ? `${match.home_score ?? "–"} – ${match.away_score ?? "–"}`
            : "vs"}
        </b>
        <span>
          <ClubCrest src={match.away_team_crest} name={match.away_team_name} />
          {match.away_team_name}
        </span>
      </div>
      <small>
        {match.competition_name}
        <FiArrowUpRight />
      </small>
    </Link>
  );
}

export default function DashboardPulse() {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  const [clubs, setClubs] = useState([]),
    [clubsError, setClubsError] = useState("");
  const [results, setResults] = useState([]),
    [table, setTable] = useState(null),
    [league, setLeague] = useState(null);
  const [query, setQuery] = useState(""),
    [tab, setTab] = useState("upcoming"),
    [competition, setCompetition] = useState("");
  useEffect(() => {
    let active = true;
    const load = () =>
      getDashboardCommandCentre()
        .then((payload) => {
          if (active) {
            setData(payload);
            setError("");
          }
        })
        .catch(
          () =>
            active &&
            setError(
              "Matchday data is temporarily unavailable. Browse matches below.",
            ),
        );
    load();
    const timer = window.setInterval(load, 120000);
    getCompetitions()
      .then((items) => {
        const preferred =
          items.find(
            (item) => item.code === "PL" || item.name === "Premier League",
          ) || items[0];
        if (active) setLeague(preferred);
        if (preferred) return getCompetitionStandings(preferred.id);
      })
      .then((value) => active && setTable(value))
      .catch(() => {});
    getLatestMatchDate("FINISHED")
      .then((value) => {
        const date =
          typeof value === "string" ? value : value.date || value.match_date;
        if (date) return getMatchesByDate(date, "FINISHED");
      })
      .then(
        (items) =>
          active && setResults((items || []).filter((item) => item.utc_date)),
      )
      .catch(() => {});
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    let active = true;
    const refresh = () =>
      getAccountFavourites()
        .then((rows) =>
          Promise.all(
            rows
              .filter((row) => row.entity_type === "team")
              .slice(0, 8)
              .map((row) => getTeamProfile(row.entity_id).catch(() => null)),
          ),
        )
        .then((profiles) => {
          if (active) {
            setClubs(
              profiles.filter(Boolean).map((profile) => ({
                ...profile,
                upcoming_fixtures: (profile.upcoming_fixtures || []).filter(
                  (fixture) => {
                    const date = fixtureDate(fixture.utc_date);
                    return date && date.getTime() > Date.now();
                  },
                ),
              })),
            );
            setClubsError("");
          }
        })
        .catch(
          () =>
            active &&
            setClubsError("Your saved clubs are temporarily unavailable."),
        );
    refresh();
    window.addEventListener("football-favourites-updated", refresh);
    return () => {
      active = false;
      window.removeEventListener("football-favourites-updated", refresh);
    };
  }, []);
  const featured = normaliseFixture(data?.featured);
  const forecast = useFixtureForecast(featured);
  const fixtures = useMemo(
    () =>
      (tab === "results"
        ? results
        : tab === "live"
          ? data?.live_matches || []
          : data?.upcoming || []
      ).map(normaliseFixture),
    [tab, data, results],
  );
  const competitions = [
    ...new Set(fixtures.map((item) => item.competition_name).filter(Boolean)),
  ];
  const visible = fixtures.filter(
    (match) =>
      (!competition || competition === match.competition_name) &&
      `${match.home_team_name} ${match.away_team_name}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  if (!data && !error) return <FootballLoader label="Opening your matchday" />;
  return (
    <div className="flood-dashboard">
      <div className="flood-club-strip">
        <strong>
          <FiStar /> Your clubs
        </strong>
        {clubs.length ? (
          clubs.map((club) => (
            <Link key={club.id} to={`/teams/${club.id}`}>
              <ClubCrest src={club.crest} name={club.name} />
              <span>{club.name}</span>
            </Link>
          ))
        ) : (
          <p>
            {clubsError ||
              "Make it your matchday. Follow your favourite clubs."}
          </p>
        )}
        <Link className="flood-club-manage" to="/teams">
          {clubs.length ? "Manage clubs" : "Find your clubs"}
          <FiArrowUpRight />
        </Link>
      </div>
      <div className="flood-dashboard-inner">
        <header className="flood-page-heading">
          <div>
            <h1>The game starts here.</h1>
            <p>Fixtures, forecasts and the clubs you live for.</p>
          </div>
          <Link className="flood-text-link" to="/following">
            Your matchday feed <FiArrowUpRight />
          </Link>
        </header>
        {error && (
          <p className="flood-alert" role="status">
            {error} <Link to="/matches">Browse fixtures</Link>
          </p>
        )}
        <div className="flood-feature-grid">
          <BroadcastMatchup match={featured} />
          <section className="flood-forecast-summary">
            <h2>The match, in probabilities.</h2>
            <p>
              {featured
                ? `${featured.home_team_name} vs ${featured.away_team_name}`
                : "The next fixture’s forecast will appear here."}
            </p>
            {forecast.loading ? (
              <p className="flood-empty" role="status">
                Reading the pre-match data…
              </p>
            ) : forecast.forecast ? (
              <OutcomeProbabilities
                forecast={forecast.forecast}
                home={featured.home_team_name}
                away={featured.away_team_name}
                compact
              />
            ) : (
              <p className="flood-empty">{forecast.error}</p>
            )}
            <footer>
              {forecast.forecast
                ? "Model estimate · probabilities are not guarantees."
                : "Availability depends on verified fixture and team history."}
              {featured && (
                <Link to={`/matches/${featured.id}`}>
                  Explore the match <FiArrowUpRight />
                </Link>
              )}
            </footer>
          </section>
        </div>
        <div className="flood-workspace">
          <section>
            <div className="flood-section-heading">
              <h2>Across the grounds</h2>
              <Link to="/matches">
                All fixtures <FiArrowUpRight />
              </Link>
            </div>
            <div className="flood-fixture-controls">
              <div
                className="flood-tabs"
                role="group"
                aria-label="Fixture view"
              >
                {[
                  ["upcoming", "Upcoming"],
                  ["live", "Live"],
                  ["results", "Results"],
                ].map(([value, label]) => (
                  <button
                    type="button"
                    key={value}
                    className={tab === value ? "selected" : ""}
                    aria-pressed={tab === value}
                    onClick={() => {
                      setTab(value);
                      setCompetition("");
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <label className="flood-search">
                <FiSearch />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Find a club or match"
                  aria-label="Find a club or match"
                />
              </label>
              <select
                aria-label="Filter competition"
                value={competition}
                onChange={(event) => setCompetition(event.target.value)}
              >
                <option value="">All competitions</option>
                {competitions.map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </select>
            </div>
            <div className="flood-fixture-feed">
              {visible.length ? (
                visible
                  .slice(0, 12)
                  .map((match) => <FixtureRow key={match.id} fixture={match} />)
              ) : (
                <div className="flood-empty">
                  <h3>
                    {query || competition
                      ? "No fixtures match those filters."
                      : tab === "live"
                        ? "No live matches in the stored feed."
                        : "No fixtures are available in this view."}
                  </h3>
                  <p>Try another view or explore the full fixture list.</p>
                  <Link to="/matches">
                    Open matches <FiArrowUpRight />
                  </Link>
                </div>
              )}
            </div>
          </section>
          <aside className="flood-sidebar">
            <section>
              <div className="flood-section-heading">
                <h2>The league picture</h2>
                <Link
                  to={league ? `/competitions/${league.id}` : "/competitions"}
                >
                  Full table <FiArrowUpRight />
                </Link>
              </div>
              <p className="flood-source">
                {league?.name || "League standings"}
                {table?.season ? ` · ${table.season}` : ""} · stored results
              </p>
              {table?.table?.length ? (
                <div className="flood-table-scroll">
                  <table className="flood-table">
                    <thead>
                      <tr>
                        <th scope="col">Pos</th>
                        <th scope="col">Club</th>
                        <th scope="col">P</th>
                        <th scope="col">Pts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {table.table.slice(0, 8).map((team, index) => (
                        <tr key={team.team_id || team.team || index}>
                          <td>{team.position ?? index + 1}</td>
                          <th scope="row">
                            <ClubCrest
                              name={team.team || team.team_name}
                              src={team.crest}
                            />
                            {team.team || team.team_name}
                          </th>
                          <td>{team.played ?? "—"}</td>
                          <td>{team.points ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="flood-empty">
                  A verified league table is not currently available.
                </p>
              )}
            </section>
            <section className="flood-club-next">
              <h2>Next for your clubs</h2>
              {clubs.some((club) => club.upcoming_fixtures?.length) ? (
                clubs
                  .filter((club) => club.upcoming_fixtures?.length)
                  .map((club) => (
                    <Link
                      key={club.id}
                      to={`/matches/${club.upcoming_fixtures[0].id}`}
                    >
                      <ClubCrest name={club.name} src={club.crest} />
                      <div>
                        <strong>{club.name}</strong>
                        <small>
                          {kickoffLabel(club.upcoming_fixtures[0].utc_date)}
                        </small>
                      </div>
                      <FiArrowUpRight />
                    </Link>
                  ))
              ) : (
                <p>Follow a club to keep its next fixture close.</p>
              )}
            </section>
          </aside>
        </div>
        <details className="flood-more-insights">
          <summary>More football intelligence</summary>
          <div className="flood-secondary-grid">
            <section>
              <h2>Saved forecasts & results</h2>
              {data?.timeline?.length ? (
                data.timeline.slice(0, 5).map((match) => (
                  <p key={match.id}>
                    <Link to={`/matches/${match.id}`}>
                      {match.home_team} {match.final_score} {match.away_team}
                    </Link>
                    <small>
                      {match.forecast
                        ? `Saved forecast: ${match.forecast}`
                        : "No saved pre-match forecast"}
                    </small>
                  </p>
                ))
              ) : (
                <p>No scored forecasts are available yet.</p>
              )}
            </section>
            <section>
              <h2>Season outlook</h2>
              <p>{data?.league_race_basis || "Basis unavailable"}</p>
              {data?.league_race?.slice(0, 5).map((team) => (
                <p key={team.team}>
                  {team.team}
                  <small>
                    {team.expected_points} projected points ·{" "}
                    {team.title_probability}% title estimate
                  </small>
                </p>
              ))}
              <Link to="/analytics">
                Open analytics <FiArrowUpRight />
              </Link>
            </section>
            <section>
              <h2>Data coverage</h2>
              <p>
                {data?.squad_coverage?.players ?? 0} stored player records
                across {data?.squad_coverage?.clubs ?? 0} clubs.
              </p>
              <p>
                {data?.squad_coverage?.last_updated
                  ? `Squad refresh: ${kickoffLabel(data.squad_coverage.last_updated)}`
                  : "Latest refresh time unavailable."}
              </p>
              <Link to="/players">
                Explore players <FiArrowUpRight />
              </Link>
              <h3>Fixture congestion</h3>
              <p>
                {data?.insights?.fixture_congestion?.matches
                  ? `${data.insights.fixture_congestion.team}: ${data.insights.fixture_congestion.matches} matches in the ${data.insights.fixture_congestion.period}.`
                  : "No congestion signal is available."}
              </p>
            </section>
          </div>
        </details>
      </div>
    </div>
  );
}
