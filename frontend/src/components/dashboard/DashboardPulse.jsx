import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboardCommandCentre } from "../../api/dashboardApi";
import { getAccountFavourites } from "../../api/accountApi";
import { getTeamProfile } from "../../api/teamApi";
import FootballLoader from "../layout/FootballLoader";

const formatKickoff = (value) => value ? new Date(value).toLocaleString(undefined, {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
}) : "Kick-off to be confirmed";

const countdown = (value) => {
    if (!value) return "Kick-off to be confirmed";
    const minutes = Math.max(0, Math.round((new Date(value).getTime() - Date.now()) / 60000));
    if (!minutes) return "Starting now";
    const days = Math.floor(minutes / 1440);
    const hours = Math.floor((minutes % 1440) / 60);
    return days ? `Starts in ${days}d ${hours}h` : `Starts in ${hours}h ${minutes % 60}m`;
};

function Crest({ src, name }) {
    return src ? <img src={src} alt="" /> : <span className="dashboard-crest-fallback">{name?.slice(0, 2)}</span>;
}

function DashboardPulse() {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");
    const [clubFixtures, setClubFixtures] = useState([]);

    useEffect(() => {
        let active = true;
        const load = () => getDashboardCommandCentre().then((payload) => {
            if (active) { setData(payload); setError(""); }
        }).catch(() => active && setError("Live dashboard data is temporarily unavailable."));
        load();
        const timer = window.setInterval(load, 120000);
        return () => { active = false; window.clearInterval(timer); };
    }, []);

    useEffect(() => {
        const refresh = () => getAccountFavourites().then((rows) => {
            const teamIds = rows.filter((row) => row.entity_type === "team").map((row) => row.entity_id);
            if (!teamIds.length) { setClubFixtures([]); return null; }
            return Promise.all(teamIds.map((id) => getTeamProfile(id).catch(() => null))).then((profiles) => {
                setClubFixtures(profiles.filter((profile) => profile?.upcoming_fixtures?.length).map((profile) => ({
                    teamName: profile.name,
                    match: profile.upcoming_fixtures[0],
                })).slice(0, 4));
            });
        }).catch(() => setClubFixtures([]));
        refresh();
        window.addEventListener("football-favourites-updated", refresh);
        return () => window.removeEventListener("football-favourites-updated", refresh);
    }, []);

    const featured = data?.featured;

    if (error) return <section className="dashboard-command"><p className="dashboard-state">{error}</p></section>;
    if (!data) return <section className="dashboard-command"><FootballLoader label="Loading the matchday centre" /></section>;

    return <main className="dashboard-command">
        <section className="dashboard-featured">
            <div className="dashboard-featured-copy">
                <span className="dashboard-kicker"><i className={data.live_matches?.length ? "is-live" : ""} />{data.insights?.featured_label || "Matchday centre"}</span>
                <h1>Football, in one place.</h1>
                <p>Live scores, fixture intelligence, season forecasts and your clubs—built from the data currently synced to your platform.</p>
                <div className="dashboard-actions"><Link to="/matches" className="dashboard-primary">Open match centre <b>→</b></Link><Link to="/predictions" className="dashboard-secondary">Explore predictions</Link></div>
            </div>
            {featured ? <article className="dashboard-featured-match">
                <header><span>{featured.competition}</span><b className={data.live_matches?.length ? "dashboard-live" : ""}>{data.live_matches?.length ? "LIVE" : formatKickoff(featured.utc_date)}</b></header>
                <div className="dashboard-fixture-teams"><section><Crest src={featured.home_crest} name={featured.home_team} /><strong>{featured.home_team}</strong></section><b className="dashboard-versus">{data.live_matches?.length ? `${featured.home_score ?? 0} – ${featured.away_score ?? 0}` : "VS"}</b><section><Crest src={featured.away_crest} name={featured.away_team} /><strong>{featured.away_team}</strong></section></div>
                <footer><span>{featured.match_week ? `Matchweek ${featured.match_week}` : "Scheduled fixture"}</span><strong>{data.live_matches?.length ? "Score updates automatically" : countdown(featured.utc_date)}</strong></footer>
            </article> : <article className="dashboard-featured-match dashboard-empty-fixture"><strong>No upcoming fixture is stored yet.</strong><span>Fixture sync will populate this area when schedules are announced.</span></article>}
        </section>

        <section className="dashboard-live-strip" aria-label="Live matches">
            <header><span><i className="is-live" /> Live matchday</span><small>{data.live_matches?.length ? `${data.live_matches.length} live match${data.live_matches.length > 1 ? "es" : ""}` : "No live matches right now"}</small></header>
            <div>{data.live_matches?.length ? data.live_matches.map((match) => <Link key={match.id} to="/matches"><strong>{match.home_team} <b>{match.home_score ?? 0}–{match.away_score ?? 0}</b> {match.away_team}</strong><span>{match.competition}</span></Link>) : (data.upcoming || []).slice(0, 4).map((match) => <Link key={match.id} to={`/matches?team=${encodeURIComponent(match.home_team)}`}><strong>{match.home_team} <i>vs</i> {match.away_team}</strong><span>{formatKickoff(match.utc_date)}</span></Link>)}</div>
        </section>

        <section className="dashboard-board">
            <article className="dashboard-panel dashboard-club-feed"><header><span>Your club feed</span><Link to="/teams">Manage clubs →</Link></header>{clubFixtures.length ? <div>{clubFixtures.map(({ teamName, match }) => <div className="dashboard-club-row" key={match.id}><Link to={`/matches?team=${encodeURIComponent(teamName)}`}><section><Crest src={match.home_crest} name={match.home_team} /><strong>{match.home_team}</strong><b>vs</b><strong>{match.away_team}</strong><Crest src={match.away_crest} name={match.away_team} /></section><small>{match.competition} · {countdown(match.utc_date)}</small></Link><Link className="dashboard-club-news" to={`/news?club=${encodeURIComponent(teamName)}`}>{teamName} news →</Link></div>)}</div> : <p>Star clubs from the Teams page to place their upcoming fixtures here.</p>}</article>
            <article className="dashboard-panel dashboard-timeline"><header><span>Forecasts now finished</span><Link to="/predictions">Prediction archive →</Link></header>{data.timeline?.length ? <div>{data.timeline.map((match) => <article key={match.id}><strong>{match.home_team} {match.final_score} {match.away_team}</strong><small>{match.forecast ? `Forecast: ${match.forecast}` : "No saved pre-kick-off forecast"}</small></article>)}</div> : <p>Completed matches will appear here with their saved forecast and final score.</p>}</article>
        </section>

        <section className="dashboard-insight-grid">
            <article className="dashboard-panel dashboard-race"><header><span>Premier League race</span><Link to="/analytics">Full analytics →</Link></header><small>{data.league_race_basis || "Season forecast"}</small>{data.league_race?.length ? <div>{data.league_race.map((team, index) => <section key={team.team}><b>{index + 1}</b><Crest src={team.crest} name={team.team} /><strong>{team.team}</strong><span>{team.expected_points} xPTS</span><em>{team.title_probability}% title</em></section>)}</div> : <p>League projections appear once fixtures and historical records are available.</p>}</article>
            <article className="dashboard-panel dashboard-signals"><header><span>Matchday signals</span><Link to="/analytics">Open analytics →</Link></header><div><section><b>Next fixtures</b><strong>{data.insights?.next_fixture_count || 0}</strong><small>stored for the current schedule</small></section><section><b>Fixture congestion</b><strong>{data.insights?.fixture_congestion?.team || "Awaiting schedule"}</strong><small>{data.insights?.fixture_congestion?.matches ? `${data.insights.fixture_congestion.matches} matches in the ${data.insights.fixture_congestion.period}` : "No short-run congestion signal"}</small></section></div></article>
            <article className="dashboard-panel dashboard-squad"><header><span>Player coverage</span><Link to="/teams">Browse squads →</Link></header><div><strong>{data.squad_coverage?.players || 0}</strong><span>current player records across {data.squad_coverage?.clubs || 0} clubs</span><small>{data.squad_coverage?.last_updated ? `Latest squad refresh: ${new Date(data.squad_coverage.last_updated).toLocaleDateString()}` : "Squad sync is waiting for provider data."}</small></div></article>
        </section>
    </main>;
}

export default DashboardPulse;
