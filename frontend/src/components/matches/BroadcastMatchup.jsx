import { Link } from "react-router-dom";
import { FiArrowUpRight } from "react-icons/fi";
import ClubCrest from "../ClubCrest";
import { fixtureDate, normaliseFixture } from "../../utils/fixturePresentation";

export default function BroadcastMatchup({ match, venue, showLink = true }) {
  const fixture = normaliseFixture(match);
  if (!fixture)
    return (
      <section className="broadcast-matchup broadcast-missing">
        <h2>The next match awaits.</h2>
        <p>No upcoming fixture is available in the current schedule.</p>
        <Link to="/matches">
          Browse stored fixtures <FiArrowUpRight />
        </Link>
        <a className="stadium-day-credit" href="/images/stadiums/credits.html#arsenal" target="_blank" rel="noopener noreferrer">Daylight photo credit</a>
      </section>
    );
  const date = fixtureDate(fixture.utc_date);
  const live = ["LIVE", "IN_PLAY", "PAUSED"].includes(fixture.status);
  const finished = ["FINISHED", "AWARDED"].includes(fixture.status);
  const status = live
    ? "Live"
    : finished
      ? "Full time"
      : ["POSTPONED", "CANCELLED", "QUARANTINED", "SUSPENDED"].includes(
            fixture.status,
          )
        ? fixture.status.replaceAll("_", " ")
        : "Kick-off";
  const homeScore = fixture.home_score ?? fixture.score?.home;
  const awayScore = fixture.away_score ?? fixture.score?.away;
  const team = (side) => {
    const name = fixture[`${side}_team_name`] || "Team to be confirmed";
    const id = fixture[`${side}_team_id`];
    const content = (
      <>
        <ClubCrest
          name={name}
          src={fixture[`${side}_team_crest`]}
          variant="broadcast"
        />
        <span className="broadcast-team-name">{name}</span>
      </>
    );
    return id ? (
      <Link className={`broadcast-team ${side}`} to={`/teams/${id}`}>
        {content}
      </Link>
    ) : (
      <div className={`broadcast-team ${side}`}>{content}</div>
    );
  };
  return (
    <section
      className="broadcast-matchup"
      aria-label={`${fixture.home_team_name} versus ${fixture.away_team_name}`}
    >
      <header>
        <span>{fixture.competition_name || "Competition to be confirmed"}</span>
        <span className={live ? "broadcast-status live" : "broadcast-status"}>
          {status}
          {fixture.match_week ? ` · Matchweek ${fixture.match_week}` : ""}
        </span>
      </header>
      <div className="broadcast-pair">
        {team("home")}
        <div className="broadcast-match-info">
          <span>
            {date
              ? date.toLocaleDateString(undefined, { weekday: "long" })
              : "Date pending"}
          </span>
          <strong>
            {live || finished
              ? `${homeScore ?? "–"} : ${awayScore ?? "–"}`
              : date
                ? date.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  })
                : "TBC"}
          </strong>
          <span>
            {date
              ? date.toLocaleDateString(undefined, {
                  day: "numeric",
                  month: "short",
                })
              : ""}
          </span>
          <small>{venue?.name || venue || "Venue not supplied"}</small>
        </div>
        {team("away")}
      </div>
      <footer>
        <span>
          {live || finished
            ? status
            : date
              ? `${Intl.DateTimeFormat().resolvedOptions().timeZone.replaceAll("_", " ")} time`
              : "Schedule awaiting confirmation"}
        </span>
        {showLink && (
          <Link className="flood-button" to={`/matches/${fixture.id}`}>
            Open match forecast <FiArrowUpRight />
          </Link>
        )}
      </footer>
      <a className="stadium-day-credit" href="/images/stadiums/credits.html#arsenal" target="_blank" rel="noopener noreferrer">Daylight photo credit</a>
    </section>
  );
}
