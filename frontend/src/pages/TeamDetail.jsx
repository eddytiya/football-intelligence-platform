import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getTeamProfile } from "../api/teamApi";
import { getAccountFavourites, removeAccountFavourite, saveAccountFavourite } from "../api/accountApi";
import "./Teams.css";

const formPoints = (form) => form.reduce((total, result) => total + (result === "W" ? 3 : result === "D" ? 1 : 0), 0);

function TeamDetail() {
    const { teamId } = useParams();
    const [team, setTeam] = useState(null);
    const [playerSearch, setPlayerSearch] = useState("");
    const [position, setPosition] = useState("All");
    const [isFollowing, setIsFollowing] = useState(false);

    useEffect(() => { getTeamProfile(teamId).then(setTeam).catch(() => setTeam(null)); }, [teamId]);
    useEffect(() => {
        getAccountFavourites().then((rows) => setIsFollowing(
            rows.some((row) => row.entity_type === "team" && String(row.entity_id) === String(teamId)),
        )).catch(() => setIsFollowing(false));
    }, [teamId]);

    const toggleFollow = () => {
        const request = isFollowing ? removeAccountFavourite("team", teamId) : saveAccountFavourite("team", teamId);
        request.then(() => {
            setIsFollowing(!isFollowing);
            window.dispatchEvent(new Event("football-favourites-updated"));
        }).catch(() => {});
    };

    const positions = useMemo(() => ["All", ...new Set((team?.players || []).map((player) => player.position))], [team]);
    const visiblePlayers = useMemo(() => (team?.players || []).filter((player) => (
        (position === "All" || player.position === position)
        && `${player.name} ${player.nationality || ""}`.toLowerCase().includes(playerSearch.toLowerCase())
    )), [team, position, playerSearch]);
    const formSignal = useMemo(() => {
        const points = formPoints(team?.form || []);
        return { points, trend: points >= 10 ? "Improving" : points <= 4 ? "Under pressure" : "Stable" };
    }, [team]);

    if (team === null) return <MainLayout><FootballLoader label="Loading team centre" /></MainLayout>;

    return <MainLayout><section className="teams-page team-detail-page">
        <Link className="team-back" to="/teams">← All teams</Link>
        <header className="team-profile-hero">
            <div>{team.crest ? <img src={team.crest} alt="" /> : <b>{team.tla}</b>}<section><span>{team.competitions.map((item) => item.name).join(" · ") || "Football club"}</span><h1>{team.name}</h1><p>{team.venue || "Venue information pending"}{team.founded ? ` · Founded ${team.founded}` : ""}</p></section>
                <button type="button" className={`team-favourite team-profile-favourite ${isFollowing ? "is-saved" : ""}`} onClick={toggleFollow} aria-label={isFollowing ? `Unfollow ${team.name}` : `Follow ${team.name}`} title={isFollowing ? "Following" : "Follow this club"}>★</button>
            </div>
            <div className="team-profile-form"><span>Last 5</span><strong>{team.form.map((result, index) => <i className={`team-form-${result}`} key={`${result}-${index}`}>{result}</i>)}</strong></div>
        </header>
        <section className="team-profile-stats"><article><b>{team.form_summary.wins}</b><span>Wins / last 5</span></article><article><b>{team.form_summary.goals_for}</b><span>Goals scored</span></article><article><b>{team.form_summary.goals_against}</b><span>Goals conceded</span></article><article><b>{team.upcoming_fixtures.length}</b><span>Upcoming fixtures</span></article></section>
        {team.honours && <section className="team-honours-panel"><header><div><span>Club heritage</span><h2>{team.honours.recorded_honours} recorded honours</h2></div><small>Verified {team.honours.verified_on}</small></header><div>{team.honours.kind === "national" ? <><article><b>{team.honours.league_titles}</b><span>Continental titles</span></article><article><b>{team.honours.continental_titles}</b><span>World titles</span></article><article><b>{team.honours.super_cups}</b><span>Other international</span></article></> : <><article><b>{team.honours.league_titles}</b><span>League titles</span></article><article><b>{team.honours.domestic_cups}</b><span>Domestic cups</span></article><article><b>{team.honours.continental_titles}</b><span>Continental titles</span></article><article><b>{team.honours.world_titles}</b><span>World titles</span></article><article><b>{team.honours.super_cups}</b><span>Super cups</span></article></>}</div><footer>{team.honours.definition}<em>{team.honours.source}</em></footer></section>}
        <section className="team-form-insight">
            <div><span>Form trend</span><strong>{formSignal.trend}</strong><small>{formSignal.points} points from the last five</small></div>
            <div className="team-strength-track"><span>Attack momentum</span><i><b style={{ width: `${Math.min(100, team.form_summary.goals_for * 14)}%` }} /></i><span>Defensive control</span><i><b style={{ width: `${Math.max(8, 100 - team.form_summary.goals_against * 12)}%` }} /></i></div>
            <div className="team-availability"><span>Squad availability</span><strong>Stored squad active</strong><small>Injury and confirmed line-up feeds are not connected yet.</small></div>
        </section>
        <div className="team-detail-layout">
            <section className="team-detail-panel"><header><span>Upcoming fixtures</span><h2>Next matches</h2></header>{team.upcoming_fixtures.map((match) => <div className="team-fixture-row" key={match.id}><span>{match.competition} · MW {match.match_week || "—"}</span><strong>{match.home_team} <i>vs</i> {match.away_team}</strong><small>{new Date(match.utc_date).toLocaleString()}</small></div>)}{!team.upcoming_fixtures.length && <p>No upcoming fixtures.</p>}</section>
            <section className="team-detail-panel"><header><span>Recent results</span><h2>Last five matches</h2></header>{team.recent_results.map((match) => <div className="team-fixture-row" key={match.id}><span>{match.competition}</span><strong>{match.home_team} <i>{match.home_score}–{match.away_score}</i> {match.away_team}</strong><small>{new Date(match.utc_date).toLocaleDateString()}</small></div>)}{!team.recent_results.length && <p>No completed results yet.</p>}</section>
        </div>
        <section className="team-squad-panel"><header><div><span>Current stored squad</span><h2>Players ({team.players.length})</h2><p>Only players currently available in the local database are shown.</p></div><div className="team-squad-controls"><input value={playerSearch} onChange={(event) => setPlayerSearch(event.target.value)} placeholder="Search player..." /><select value={position} onChange={(event) => setPosition(event.target.value)}>{positions.map((item) => <option key={item}>{item}</option>)}</select></div></header>{visiblePlayers.length ? <div className="team-player-grid">{visiblePlayers.map((player, index) => <article key={player.id} style={{ animationDelay: `${Math.min(index, 12) * 35}ms` }}><b>{player.shirt_number || "—"}</b><div><strong>{player.name}</strong><span>{player.position}</span></div><small>{player.nationality || "Nationality unavailable"}</small><em>{player.age ? `${player.age} yrs` : "Age unavailable"}</em></article>)}</div> : <div className="team-squad-empty">No stored players match this filter.</div>}</section>
    </section></MainLayout>;
}

export default TeamDetail;
