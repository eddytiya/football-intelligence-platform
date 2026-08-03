import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import MatchCard from "../components/matches/MatchCard";
import CompetitionIntelligencePanel from "../components/competitions/CompetitionIntelligencePanel";
import { getCompetitions } from "../api/competitionApi";
import { getTeams } from "../api/teamApi";
import { getCompetitionIntelligence, getCompetitionMatchweeks, getCompetitionSeasonOutlook, getCompetitionStandings, getMatchesByMatchweek } from "../api/matchApi";
import "./CompetitionDetail.css";

const formClass = (result) => ({ W: "form-win", D: "form-draw", L: "form-loss" }[result] || "");

function CompetitionDetail() {
    const { competitionId } = useParams();
    const [competition, setCompetition] = useState(null);
    const [fixtures, setFixtures] = useState([]);
    const [matchweeks, setMatchweeks] = useState([]);
    const [selectedMatchweek, setSelectedMatchweek] = useState("");
    const [fixtureStatus, setFixtureStatus] = useState("SCHEDULED");
    const [standings, setStandings] = useState({ season: null, table: [], is_live: false });
    const [intelligence, setIntelligence] = useState(null);
    const [seasonOutlook, setSeasonOutlook] = useState(null);
    const [competitionTeams, setCompetitionTeams] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const id = Number(competitionId);
        Promise.all([getCompetitions(), getCompetitionStandings(id), getCompetitionIntelligence(id), getCompetitionSeasonOutlook(id)])
            .then(([competitions, table, insights, outlook]) => {
                setCompetition(competitions.find((item) => item.id === id) || null);
                setStandings(table);
                setIntelligence(insights);
                setSeasonOutlook(outlook);
            })
            .catch(() => setCompetition(null))
            .finally(() => setLoading(false));
    }, [competitionId]);

    useEffect(() => {
        getTeams({ competitionId: Number(competitionId) })
            .then(setCompetitionTeams)
            .catch(() => setCompetitionTeams([]));
    }, [competitionId]);

    useEffect(() => {
        let active = true;
        const id = Number(competitionId);
        setFixtures([]);
        setSelectedMatchweek("");
        getCompetitionMatchweeks(id, fixtureStatus).then(async (weeks) => {
            if (!active) return;
            setMatchweeks(weeks);
            const firstWeek = weeks[0];
            if (!firstWeek) return;
            setSelectedMatchweek(String(firstWeek));
            const matches = await getMatchesByMatchweek(id, firstWeek, fixtureStatus);
            if (active) setFixtures(matches);
        }).catch(() => active && setMatchweeks([]));
        return () => { active = false; };
    }, [competitionId, fixtureStatus]);

    const changeMatchweek = async (week) => {
        setSelectedMatchweek(week);
        setFixtures(week ? await getMatchesByMatchweek(Number(competitionId), week, fixtureStatus) : []);
    };

    const dashboard = useMemo(() => {
        const table = standings.table;
        if (!table.length) return null;
        const topAttack = [...table].sort((a, b) => b.goals_for - a.goals_for || b.points - a.points)[0];
        const bestDefence = [...table].sort((a, b) => a.goals_against - b.goals_against || b.points - a.points)[0];
        const signalRows = table.slice(0, 3).map((team) => ({ ...team, signal: Math.max(1, team.points * 4 + team.goal_difference * 1.4 + team.form.filter((item) => item === "W").length * 2) }));
        const totalSignal = signalRows.reduce((total, team) => total + team.signal, 0);
        return { leader: table[0], topAttack, bestDefence, projection: signalRows.map((team) => ({ ...team, probability: Math.round((team.signal / totalSignal) * 100) })) };
    }, [standings.table]);

    if (loading) return <MainLayout><FootballLoader label="Opening the league centre" /></MainLayout>;
    if (!competition) return <MainLayout><section className="competition-detail-page competition-not-found"><h1>Competition not found</h1><Link to="/competitions">Back to competitions</Link></section></MainLayout>;

    return <MainLayout>
        <section className="competition-detail-page">
            <Link className="back-to-competitions" to="/competitions">← All competitions</Link>
            <header className="competition-detail-hero">
                <div className="competition-detail-identity"><div>{competition.emblem ? <img src={competition.emblem} alt="" /> : competition.code}</div><section><span>{competition.area_name} · {competition.type}</span><h1>{competition.name}</h1><p>Fixtures, matchweek coverage, live table and data-driven league insights.</p></section></div>
                <div className="competition-detail-counts"><span><b>{competition.scheduled_match_count}</b> upcoming fixtures</span><span><b>{matchweeks.length || "—"}</b> matchweeks</span></div>
            </header>

            <div className="competition-detail-tabs"><button className="is-active">League centre</button><span><i /> Live data sync enabled</span></div>

            <section className="competition-clubs-panel">
                <header><div><span>Club directory</span><h2>Teams in {competition.name}</h2></div><b>{competitionTeams.length} teams</b></header>
                <div className="competition-clubs-grid">
                    {competitionTeams.map((team) => <Link className="competition-club-link" to={`/teams/${team.id}`} key={team.id} title={`Open ${team.name} team profile`}>
                        {team.crest ? <img src={team.crest} alt="" /> : <i>{team.tla || team.name.slice(0, 2)}</i>}<span>{team.name}</span><em>Open team ›</em>
                    </Link>)}
                </div>
            </section>

            <section className="competition-insight-grid">
                <article><span>Current leader</span><strong>{dashboard?.leader?.team || "Awaiting kick-off"}</strong><small>{dashboard ? `${dashboard.leader.points} pts · ${dashboard.leader.played} played` : "Table begins after the first final result"}</small></article>
                <article><span>Best attack</span><strong>{dashboard?.topAttack?.team || "—"}</strong><small>{dashboard ? `${dashboard.topAttack.goals_for} goals scored` : "Live scoring data required"}</small></article>
                <article><span>Best defence</span><strong>{dashboard?.bestDefence?.team || "—"}</strong><small>{dashboard ? `${dashboard.bestDefence.goals_against} goals conceded` : "Live scoring data required"}</small></article>
                <article className="competition-projection-card"><span>Season outlook</span><strong>{dashboard?.projection?.[0] ? `${dashboard.projection[0].team} ${dashboard.projection[0].probability}%` : "Model warming up"}</strong><small>{dashboard ? "Form, points and goal difference signal" : "Needs completed league matches"}</small></article>
            </section>

            <section className="competition-season-forecast">
                <header className="competition-season-forecast__header">
                    <div>
                        <span>{seasonOutlook?.season || "Season"} forecast</span>
                        <h2>Predicted {competition.name} table</h2>
                        <p>Five completed seasons, team strength and current form combined into one season outlook.</p>
                    </div>
                    {seasonOutlook?.historical_seasons_used?.length > 0 && <b>{seasonOutlook.historical_seasons_used.length} seasons used</b>}
                </header>
                {seasonOutlook?.forecast?.length > 0 ? (
                    <div className="competition-forecast-grid">
                        {seasonOutlook.forecast.map((team) => <article className="competition-forecast-row" key={team.team_id || team.team}>
                            <strong className="competition-forecast-position">{team.projected_position}</strong>
                            {team.crest ? <img src={team.crest} alt="" /> : <i>{team.team?.slice(0, 2)}</i>}
                            <div><strong>{team.team}</strong><small>{Number(team.historical_ppg || 0).toFixed(2)} projected PPG</small></div>
                            <b>{Number(team.projected_points || 0).toFixed(1)} pts</b>
                        </article>)}
                    </div>
                ) : <p className="competition-forecast-empty">{seasonOutlook?.message || "The forecast will appear once enough historical results are available."}</p>}
            </section>

            <div className="competition-detail-layout">
                <main className="competition-fixtures-panel">
                    <div className="competition-panel-heading"><div><span>{fixtureStatus === "SCHEDULED" ? "Upcoming" : "Completed"} · {selectedMatchweek ? `Matchweek ${selectedMatchweek}` : "No matchweek"}</span><h2>{selectedMatchweek ? `${fixtures.length} ${fixtureStatus === "SCHEDULED" ? "upcoming fixtures" : "completed matches"}` : "Choose a matchweek"}</h2></div><div className="competition-fixture-controls"><div className="competition-status-switch"><button className={fixtureStatus === "SCHEDULED" ? "is-active" : ""} onClick={() => setFixtureStatus("SCHEDULED")}>Upcoming</button><button className={fixtureStatus === "FINISHED" ? "is-active" : ""} onClick={() => setFixtureStatus("FINISHED")}>Completed</button></div><select value={selectedMatchweek} onChange={(event) => changeMatchweek(event.target.value)}><option value="">Select matchweek</option>{matchweeks.map((week) => <option key={week} value={week}>Matchweek {week}</option>)}</select></div></div>
                    <div className="competition-fixtures-list">{fixtures.map((match) => <MatchCard key={match.id} match={match} />)}{fixtures.length === 0 && <p className="competition-empty-fixtures">No {fixtureStatus === "SCHEDULED" ? "upcoming" : "completed"} matches for this matchweek.</p>}</div>
                </main>
                <aside className="competition-standings-panel">
                    <div className="competition-panel-heading"><div><span>{standings.is_live ? "Live table" : "Season table"}</span><h2>{standings.season || "Standings"}</h2></div><small>{standings.is_live ? "Recalculated from synced results" : "Available after the first result"}</small></div>
                    {standings.table.length > 0 ? <><div className="competition-table-labels"><span>Club</span><span>Form</span><span>P</span><span>GD</span><span>Pts</span></div><ol>{standings.table.map((team) => <li key={`${team.position}-${team.team}`}><b>{team.position}</b>{team.crest && <img src={team.crest} alt="" />}<span>{team.team}</span><div className="standings-form">{team.form.map((result, index) => <i className={formClass(result)} key={`${result}-${index}`}>{result}</i>)}</div><em>{team.played}</em><em>{team.goal_difference > 0 ? `+${team.goal_difference}` : team.goal_difference}</em><strong>{team.points}</strong></li>)}</ol></> : <p className="competition-empty-fixtures">The new-season table will appear once results are available.</p>}
                </aside>
            </div>

            <section className="competition-race-panel"><div><span>Data-driven race view</span><h2>Title contenders</h2><p>This early-season projection is based on the live table, goal difference, and recent form. It strengthens as more results arrive.</p></div>{dashboard?.projection?.length ? <div className="competition-race-bars">{dashboard.projection.map((team) => <div key={team.team}><span>{team.team}</span><i><b style={{ width: `${team.probability}%` }} /></i><strong>{team.probability}%</strong></div>)}</div> : <div className="competition-race-empty">Results from the opening matchweek will unlock the league projection.</div>}</section>
            <CompetitionIntelligencePanel intelligence={intelligence} />
        </section>
    </MainLayout>;
}

export default CompetitionDetail;
