import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getCompetitions } from "../api/competitionApi";
import { getTeamComparison, getTeamProfile, getTeams } from "../api/teamApi";
import { getAccountFavourites, removeAccountFavourite, saveAccountFavourite } from "../api/accountApi";
import "./Teams.css";

const resultCount = (form, result) => (form || []).filter((item) => item === result).length;

function FormBadges({ form, alignRight = false }) {
    if (!form?.length) return <strong>—</strong>;
    return <strong className={`comparison-form${alignRight ? " comparison-form-away" : ""}`}>{form.map((result, index) => <i className={`team-form-${result}`} key={`${result}-${index}`}>{result}</i>)}</strong>;
}

function ClubPicker({ label, value, setValue, selected, setSelected }) {
    const [suggestions, setSuggestions] = useState([]);
    const [searching, setSearching] = useState(false);

    useEffect(() => {
        const term = value.trim();
        if (term.length < 2 || selected) { setSuggestions([]); return undefined; }
        let active = true;
        const timer = setTimeout(() => {
            setSearching(true);
            getTeams({ query: term, limit: 25 }).then((results) => {
                if (!active) return;
                const ranked = [...results].sort((a, b) => {
                    const score = (team) => Number(Boolean(team.crest)) + Number(team.competitions?.length > 0) + Number(Boolean(team.next_match));
                    return score(b) - score(a) || a.name.localeCompare(b.name);
                });
                setSuggestions(ranked.slice(0, 6));
            }).catch(() => active && setSuggestions([])).finally(() => active && setSearching(false));
        }, 220);
        return () => { active = false; clearTimeout(timer); };
    }, [value, selected]);

    return <label className="club-picker">
        <span>{label}</span>
        <input value={value} onChange={(event) => { setValue(event.target.value); setSelected(""); }} placeholder={`Type ${label.toLowerCase()}...`} />
        {searching && !selected && <em className="club-picker-status">Searching clubs…</em>}
        {suggestions.length > 0 && !selected && <div className="club-picker-menu">{suggestions.map((team) => <button type="button" key={team.id} onClick={() => { setSelected(String(team.id)); setValue(team.name); }}>
            {team.crest ? <img src={team.crest} alt="" /> : <b>{team.tla || team.name.slice(0, 2)}</b>}
            <span>{team.name}<small>{team.competitions?.map((competition) => competition.name).join(" · ") || "Historical record"}</small></span>
        </button>)}</div>}
    </label>;
}

const TEAMS_PAGE_SIZE = 100;

function Teams() {
    const [teams, setTeams] = useState([]);
    const [competitions, setCompetitions] = useState([]);
    const [search, setSearch] = useState("");
    const [competitionId, setCompetitionId] = useState("");
    const [favourites, setFavourites] = useState([]);
    const [compareHomeSearch, setCompareHomeSearch] = useState("");
    const [compareAwaySearch, setCompareAwaySearch] = useState("");
    const [compareHomeId, setCompareHomeId] = useState("");
    const [compareAwayId, setCompareAwayId] = useState("");
    const [comparisonProfiles, setComparisonProfiles] = useState([]);
    const [headToHead, setHeadToHead] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(false);

    useEffect(() => { getCompetitions().then(setCompetitions).catch(() => setCompetitions([])); }, []);
    useEffect(() => {
        getAccountFavourites().then((rows) => setFavourites(
            rows.filter((row) => row.entity_type === "team").map((row) => row.entity_id),
        )).catch(() => setFavourites([]));
    }, []);
    useEffect(() => {
        let active = true;
        const timer = setTimeout(() => {
            setLoading(true);
            getTeams({ query: search, competitionId, limit: TEAMS_PAGE_SIZE }).then((data) => {
                if (!active) return;
                setTeams(data);
                setHasMore(data.length === TEAMS_PAGE_SIZE);
            }).catch(() => active && setTeams([])).finally(() => active && setLoading(false));
        }, 180);
        return () => { active = false; clearTimeout(timer); };
    }, [search, competitionId]);

    const loadMoreTeams = () => {
        setLoadingMore(true);
        getTeams({ query: search, competitionId, limit: TEAMS_PAGE_SIZE, offset: teams.length }).then((data) => {
            setTeams((current) => [...current, ...data]);
            setHasMore(data.length === TEAMS_PAGE_SIZE);
        }).catch(() => setHasMore(false)).finally(() => setLoadingMore(false));
    };
    useEffect(() => {
        if (!compareHomeId || !compareAwayId || compareHomeId === compareAwayId) { setComparisonProfiles([]); setHeadToHead(null); return; }
        let active = true;
        Promise.all([getTeamProfile(compareHomeId), getTeamProfile(compareAwayId), getTeamComparison(compareHomeId, compareAwayId)]).then(([first, second, comparison]) => {
            if (!active) return;
            setComparisonProfiles([first, second]);
            setHeadToHead(comparison);
        }).catch(() => { if (active) { setComparisonProfiles([]); setHeadToHead(null); } });
        return () => { active = false; };
    }, [compareHomeId, compareAwayId]);

    const visibleTeams = useMemo(() => [...teams].sort((a, b) => Number(favourites.includes(b.id)) - Number(favourites.includes(a.id)) || a.name.localeCompare(b.name)), [teams, favourites]);
    const [homeProfile, awayProfile] = comparisonProfiles;
    const toggleFavourite = (id) => {
        const isFollowing = favourites.includes(id);
        const request = isFollowing ? removeAccountFavourite("team", id) : saveAccountFavourite("team", id);
        request.then(() => {
            setFavourites((current) => isFollowing ? current.filter((item) => item !== id) : [...current, id]);
            window.dispatchEvent(new Event("football-favourites-updated"));
        }).catch(() => {});
    };

    if (loading) return <MainLayout><FootballLoader label="Loading club directory" /></MainLayout>;

    return <MainLayout><section className="teams-page">
        <header className="teams-hero"><div><span>Club intelligence directory</span><h1>Teams</h1><p>Search every tracked club, follow its form, and move from a team into fixtures, results, and prediction insights.</p></div><div className="teams-hero-stat"><b>{teams.length}</b><span>clubs in this view</span></div></header>
        <div className="teams-controls"><label><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search a club, e.g. Barcelona or Arsenal..." /></label><select value={competitionId} onChange={(event) => setCompetitionId(event.target.value)}><option value="">All competitions</option>{competitions.map((competition) => <option key={competition.id} value={competition.id}>{competition.name}</option>)}</select><button onClick={() => { setSearch(""); setCompetitionId(""); }}>Reset</button></div>
        <div className="teams-directory-meta"><span><i /> Live fixture and result data</span><b>{visibleTeams.length} results</b></div>

        <section className="team-compare-panel team-compare-expanded">
            <div><span>Club comparison</span><h2>Compare two clubs</h2><p>Type each name to search every club in the database, then compare form, trophies, results and head-to-head history.</p></div>
            <div className="team-compare-controls"><ClubPicker label="First club" value={compareHomeSearch} setValue={setCompareHomeSearch} selected={compareHomeId} setSelected={setCompareHomeId} /><b>vs</b><ClubPicker label="Second club" value={compareAwaySearch} setValue={setCompareAwaySearch} selected={compareAwayId} setSelected={setCompareAwayId} /></div>
            {homeProfile && awayProfile && <div className="team-comparison-table">
                <header><Link to={`/teams/${homeProfile.id}`}>{homeProfile.crest && <img src={homeProfile.crest} alt="" />}<strong>{homeProfile.name}</strong></Link><span>Comparison</span><Link to={`/teams/${awayProfile.id}`}>{awayProfile.crest && <img src={awayProfile.crest} alt="" />}<strong>{awayProfile.name}</strong></Link></header>
                <div><FormBadges form={homeProfile.form} /><span>Recent form<br />last five</span><FormBadges form={awayProfile.form} alignRight /></div>
                <div><strong>{homeProfile.form.length}</strong><span>Matches played<br />last five</span><strong>{awayProfile.form.length}</strong></div>
                <div><strong>{resultCount(homeProfile.form, "W")}W · {resultCount(homeProfile.form, "D")}D · {resultCount(homeProfile.form, "L")}L</strong><span>Win / draw / loss</span><strong>{resultCount(awayProfile.form, "W")}W · {resultCount(awayProfile.form, "D")}D · {resultCount(awayProfile.form, "L")}L</strong></div>
                <div><strong>{homeProfile.form_summary.goals_for} – {homeProfile.form_summary.goals_against}</strong><span>Goals for / against</span><strong>{awayProfile.form_summary.goals_for} – {awayProfile.form_summary.goals_against}</strong></div>
                <div><strong>{homeProfile.honours?.recorded_honours ?? "—"}</strong><span>Recorded honours</span><strong>{awayProfile.honours?.recorded_honours ?? "—"}</strong></div>
                <div><strong>{homeProfile.upcoming_fixtures.length}</strong><span>Upcoming fixtures</span><strong>{awayProfile.upcoming_fixtures.length}</strong></div>
                {headToHead && <><div><strong>{headToHead.meetings}</strong><span>Head-to-head meetings<br />last decade</span><strong>{headToHead.meetings}</strong></div><div><strong>{headToHead.first_team_wins}W · {headToHead.draws}D · {headToHead.second_team_wins}L</strong><span>Head-to-head<br />win / draw / loss</span><strong>{headToHead.second_team_wins}W · {headToHead.draws}D · {headToHead.first_team_wins}L</strong></div></>}
            </div>}
            {homeProfile && awayProfile && headToHead && <section className="team-head-to-head">
                <header><div><span>Head to head</span><h3>{headToHead.meetings ? `${headToHead.meetings} completed meeting${headToHead.meetings === 1 ? "" : "s"} in the ${headToHead.period}` : `No completed meetings in the ${headToHead.period}`}</h3></div>{headToHead.meetings > 0 && <small>Goals: {headToHead.first_team_goals} – {headToHead.second_team_goals}</small>}</header>
                {headToHead.meetings > 0 ? <><div className="head-to-head-record"><strong>{headToHead.first_team_wins}<small>{homeProfile.name} wins</small></strong><b>{headToHead.draws}<small>draws</small></b><strong>{headToHead.second_team_wins}<small>{awayProfile.name} wins</small></strong></div><div className="head-to-head-meetings">{headToHead.recent_meetings.map((match) => <article key={match.id}><small>{match.competition || "Competition"} · {new Date(match.utc_date).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</small><strong>{match.home_team} <b>{match.home_score}–{match.away_score}</b> {match.away_team}</strong></article>)}</div></> : <p>These clubs have never played each other in the stored results from the last decade.</p>}
            </section>}
        </section>

        {loading ? <div className="team-skeleton-grid">{Array.from({ length: 9 }).map((_, index) => <i key={index} />)}</div> : <div className="team-grid">{visibleTeams.map((team, index) => <article className="team-card" key={team.id} style={{ animationDelay: `${Math.min(index, 8) * 45}ms` }}><button className={`team-favourite ${favourites.includes(team.id) ? "is-saved" : ""}`} onClick={() => toggleFavourite(team.id)} aria-label={`Favourite ${team.name}`}>★</button><div className="team-card-identity">{team.crest ? <img src={team.crest} alt="" /> : <b>{team.tla || team.name.slice(0, 2)}</b>}<div><h2>{team.name}</h2><p>{team.competitions.map((item) => item.name).slice(0, 2).join(" · ") || "Tracked club"}</p></div></div><div className="team-card-form"><span>Recent form</span><div>{team.form.length ? team.form.map((result, formIndex) => <i className={`team-form-${result}`} key={`${result}-${formIndex}`}>{result}</i>) : <small>Awaiting results</small>}</div></div>{team.next_match ? <div className="team-next-match"><span>Next fixture</span><strong>{team.next_match.home_team} <i>vs</i> {team.next_match.away_team}</strong><small>{new Date(team.next_match.utc_date).toLocaleDateString(undefined, { day: "numeric", month: "short" })} · MW {team.next_match.match_week || "—"}</small></div> : <div className="team-next-match is-empty"><span>Next fixture</span><strong>No scheduled fixture</strong></div>}<Link to={`/teams/${team.id}`}>Open team centre <b>→</b></Link></article>)}</div>}
        {!loading && !visibleTeams.length && <div className="teams-empty">No clubs match that search. Try a different team or competition.</div>}
        {!loading && hasMore && <div className="teams-load-more"><button type="button" onClick={loadMoreTeams} disabled={loadingMore}>{loadingMore ? "Loading…" : "Load more clubs"}</button></div>}
    </section></MainLayout>;
}

export default Teams;
