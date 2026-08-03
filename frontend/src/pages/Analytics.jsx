import { useEffect, useMemo, useState } from "react";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getCompetitions, getDecadeTopScorers } from "../api/competitionApi";
import { getCompetitionIntelligence, getCompetitionMatchweeks, getCompetitionStandings, getMatchesByMatchweek, getCompetitionSeasonOutlook } from "../api/matchApi";
import { getTeamComparison, getTeams } from "../api/teamApi";
import "./Analytics.css";

const formChip = (result, index) => <i className={`analytics-form-chip ${result.toLowerCase()}`} key={`${result}-${index}`}>{result}</i>;
const number = (value) => Number(value || 0).toFixed(1);

function Analytics() {
    const [competitions, setCompetitions] = useState([]);
    const [competitionId, setCompetitionId] = useState("");
    const [intelligence, setIntelligence] = useState(null);
    const [standings, setStandings] = useState([]);
    const [teams, setTeams] = useState([]);
    const [matchweeks, setMatchweeks] = useState([]);
    const [matchweek, setMatchweek] = useState("");
    const [review, setReview] = useState([]);
    const [firstTeamId, setFirstTeamId] = useState("");
    const [secondTeamId, setSecondTeamId] = useState("");
    const [headToHead, setHeadToHead] = useState(null);
    const [scorerData, setScorerData] = useState(null);
    const [loadingScorers, setLoadingScorers] = useState(false);
    const [seasonOutlook, setSeasonOutlook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        getCompetitions().then((data) => {
            setCompetitions(data);
            const preferred = data.find((item) => item.name === "Premier League") || data[0];
            setCompetitionId(preferred ? String(preferred.id) : "");
        }).catch(() => setError("Competition data is unavailable right now.")).finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        if (!competitionId) return;
        setLoading(true); setError(""); setIntelligence(null); setReview([]); setScorerData(null); setSeasonOutlook(null);
        Promise.all([
            getCompetitionIntelligence(competitionId),
            getCompetitionStandings(competitionId),
            getCompetitionMatchweeks(competitionId, "SCHEDULED"),
            getTeams({ competitionId, limit: 100 }),
            getCompetitionSeasonOutlook(competitionId),
        ]).then(([intel, table, weeks, clubRows, outlook]) => {
            setIntelligence(intel); setStandings(table.table || []); setMatchweeks(weeks || []); setTeams(clubRows || []);
            setSeasonOutlook(outlook);
            setMatchweek(String((weeks || [])[0] || ""));
        }).catch(() => setError("This competition has no analytics dataset available yet.")).finally(() => setLoading(false));
    }, [competitionId]);

    useEffect(() => {
        if (!competitionId || !matchweek) return;
        getMatchesByMatchweek(competitionId, matchweek, "").then(setReview).catch(() => setReview([]));
    }, [competitionId, matchweek]);

    useEffect(() => {
        if (!firstTeamId || !secondTeamId || firstTeamId === secondTeamId) { setHeadToHead(null); return; }
        getTeamComparison(firstTeamId, secondTeamId).then(setHeadToHead).catch(() => setHeadToHead(null));
    }, [firstTeamId, secondTeamId]);

    const loadDecadeScorers = async () => {
        if (!competitionId) return;
        setLoadingScorers(true);
        try {
            setScorerData(await getDecadeTopScorers(competitionId));
            setSeasonOutlook(await getCompetitionSeasonOutlook(competitionId));
        } catch {
            setScorerData({ scorers: [], message: "Historical scorer data could not be loaded right now." });
        } finally {
            setLoadingScorers(false);
        }
    };

    const selectedCompetition = competitions.find((item) => String(item.id) === competitionId);
    const analyticsTable = intelligence?.table || [];
    const isPreSeason = Boolean(analyticsTable.length) && (intelligence?.data_coverage || 0) === 0;
    const bestAttack = useMemo(() => [...analyticsTable].sort((a, b) => b.attack_rating - a.attack_rating)[0], [analyticsTable]);
    const bestDefence = useMemo(() => [...analyticsTable].sort((a, b) => a.defence_rating - b.defence_rating)[0], [analyticsTable]);
    const completedReview = review.filter((match) => ["FINISHED", "AWARDED"].includes(match.status));
    const highestScoring = [...completedReview].sort((a, b) => (b.home_score + b.away_score) - (a.home_score + a.away_score))[0];
    const fixtureDifficulty = useMemo(() => [...analyticsTable].map((row) => ({ ...row, average_difficulty: row.fixture_difficulty?.length ? row.fixture_difficulty.reduce((total, fixture) => total + fixture.difficulty, 0) / row.fixture_difficulty.length : 0 })).sort((a, b) => b.average_difficulty - a.average_difficulty), [analyticsTable]);
    const homeAwayLeaders = useMemo(() => [...analyticsTable].filter((row) => row.home_record?.played || row.away_record?.played).sort((a, b) => ((b.home_record?.points || 0) - (b.away_record?.points || 0)) - ((a.home_record?.points || 0) - (a.away_record?.points || 0))).slice(0, 6), [analyticsTable]);

    return <MainLayout><section className="analytics-page">
        <header className="analytics-hero"><div><span>Performance room</span><h1>Football Analytics</h1><p>Live competition intelligence built from stored results, scheduled fixtures and the same team-strength model used across the platform.</p></div><aside><small>DATA COVERAGE</small><strong>{intelligence?.data_coverage || 0}</strong><span>completed matches</span></aside></header>

        <section className="analytics-controls"><label>Competition<select value={competitionId} onChange={(event) => setCompetitionId(event.target.value)}>{competitions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Matchweek<select value={matchweek} onChange={(event) => setMatchweek(event.target.value)}><option value="">All available</option>{matchweeks.map((week) => <option key={week} value={week}>Matchweek {week}</option>)}</select></label><span>{selectedCompetition?.area_name || "World football"} · {intelligence?.season || "Current season"}</span></section>

        {loading ? <FootballLoader label="Building the analytics board" /> : error ? <div className="analytics-loading">{error}</div> : <>
            <section className="analytics-stat-grid"><article><span>{isPreSeason ? "Forecast leader" : "League leader"}</span><strong>{analyticsTable[0]?.team || "Awaiting results"}</strong><small>{isPreSeason ? `${analyticsTable[0]?.expected_points || 0} expected points` : `${analyticsTable[0]?.points || 0} points`}</small></article><article><span>Best attack</span><strong>{bestAttack?.team || "Awaiting results"}</strong><small>{bestAttack ? `${number(bestAttack.attack_rating)} attack rating` : "—"}</small></article><article><span>Best defence</span><strong>{bestDefence?.team || "Awaiting results"}</strong><small>{bestDefence ? `${number(bestDefence.defence_rating)} defence rating` : "—"}</small></article><article><span>Simulations</span><strong>{intelligence?.simulations || 0}</strong><small>season projections</small></article></section>

            <section className="analytics-layout"><article className="analytics-table-panel"><header><div><span>{isPreSeason ? "Pre-season forecast" : "Live league table"}</span><h2>{intelligence?.season || "Season table"}</h2></div><small>{isPreSeason ? `${intelligence?.strength_basis || "Historical strength"} + fixture simulations` : (standings.length ? "Updates from completed results" : "Table appears after the first result")}</small></header>{analyticsTable.length ? <div className="analytics-table">{analyticsTable.map((row, index) => <div key={row.team}><b>{index + 1}</b>{row.crest ? <img src={row.crest} alt="" /> : <i /> }<strong>{row.team}</strong><span>{row.played} GP</span><span>{isPreSeason ? `${row.historical_ppg} hist. PPG` : `${row.goals_for}–${row.goals_against}`}</span><em>{isPreSeason ? `${row.expected_points} xPTS` : `${row.points} PTS`}</em></div>)}</div> : <p className="analytics-empty">No completed results yet. The simulation and scheduled-fixture analysis remain available.</p>}</article>
                <article className="analytics-race-panel"><header><span>League race</span><h2>Projected outcomes</h2><small>Simulation-led estimates, not guarantees.</small></header>{analyticsTable.slice(0, 6).map((row) => <div className="analytics-race-row" key={row.team}><div><strong>{row.team}</strong><span>Expected {row.expected_position}th · range {row.rank_range?.join("–")}</span></div><b style={{ "--race": `${Math.max(row.title_probability, row.top_four_probability)}%` }}>{row.title_probability > 0 ? `${row.title_probability}% title` : `${row.top_four_probability}% top four`}</b></div>)}<footer>{analyticsTable.slice(-3).map((row) => <span key={row.team}>{row.team}: {row.relegation_probability}% relegation risk</span>)}</footer></article></section>

            <section className="analytics-strength-panel"><header><div><span>Team strength tracker</span><h2>Attack, defence and recent momentum</h2></div><small>Ratings update as results are synced.</small></header><div>{analyticsTable.slice(0, 10).map((row) => <article key={row.team}><div><strong>{row.team}</strong><span>{row.form?.map(formChip)}</span></div><section><label>Attack <i><b style={{ width: `${Math.min(row.attack_rating * 45, 100)}%` }} /></i><em>{number(row.attack_rating)}</em></label><label>Defence <i><b style={{ width: `${Math.min((2.4 - row.defence_rating) * 60, 100)}%` }} /></i><em>{number(row.defence_rating)}</em></label><small>{row.form_trend} · xPts {row.expected_points}</small></section></article>)}</div></section>

            <section className="analytics-layout analytics-bottom"><article className="analytics-review-panel"><header><div><span>Matchweek review</span><h2>{matchweek ? `Matchweek ${matchweek}` : "Select a matchweek"}</h2></div><small>{completedReview.length} completed</small></header>{completedReview.length ? <>{highestScoring && <p className="analytics-highlight">Most goals: <b>{highestScoring.home_team_name} {highestScoring.home_score}–{highestScoring.away_score} {highestScoring.away_team_name}</b></p>}<div>{completedReview.slice(0, 8).map((match) => <p key={match.id}><span>{match.home_team_name}</span><b>{match.home_score}–{match.away_score}</b><span>{match.away_team_name}</span></p>)}</div></> : <p className="analytics-empty">Completed matches for this matchweek will appear after the live sync records final scores.</p>}</article>
                <article className="analytics-upset-panel"><header><span>Upset detector</span><h2>Upcoming underdogs</h2></header>{intelligence?.upsets?.length ? intelligence.upsets.map((match) => <div key={match.id}><strong>{match.home_team} vs {match.away_team}</strong><span>{match.underdog} has a {match.underdog_probability}% win chance</span><small>xG {match.expected_goals?.join("–")}</small></div>) : <p className="analytics-empty">No meaningful upset signals in the next scheduled fixtures.</p>}</article></section>

            <section className="analytics-new-insights"><article className="analytics-difficulty"><header><span>Fixture difficulty</span><h2>Next five-match run</h2><p>Opponent strength plus a small away-day adjustment.</p></header>{fixtureDifficulty.slice(0, 6).map((row) => <div key={row.team}><section><strong>{row.team}</strong><small>Average {number(row.average_difficulty)} / 5</small></section><aside>{row.fixture_difficulty?.map((fixture, index) => <i className={`difficulty-${fixture.difficulty}`} title={`${fixture.away ? "Away" : "Home"} vs ${fixture.opponent}`} key={`${fixture.opponent}-${index}`}>{fixture.away ? "A" : "H"}</i>)}</aside></div>)}</article>
                <article className="analytics-home-away"><header><span>Home vs away</span><h2>Where teams earn points</h2></header>{homeAwayLeaders.length ? homeAwayLeaders.map((row) => <div key={row.team}><strong>{row.team}</strong><span><b>Home</b> {row.home_record.points} pts / {row.home_record.played} GP</span><span><b>Away</b> {row.away_record.points} pts / {row.away_record.played} GP</span></div>) : <p className="analytics-empty">Home and away splits appear after the first completed results.</p>}</article>
                <article className="analytics-timeline"><header><span>Form timeline</span><h2>Last ten results</h2><p>Each marker follows the season timeline, from older to newer matches.</p></header>{analyticsTable.slice(0, 5).map((row) => <div key={row.team}><strong>{row.team}</strong><section>{row.form_timeline?.map((point, index) => <i className={point.result.toLowerCase()} title={`Matchweek ${point.week}: ${point.result}`} key={`${point.week}-${index}`}>{point.result}</i>)}</section></div>)}</article></section>

            <section className="analytics-head-to-head"><header><div><span>Head-to-head explorer</span><h2>Compare two teams</h2><p>Historical meetings, wins, draws and goals from the stored database.</p></div><div><select value={firstTeamId} onChange={(event) => setFirstTeamId(event.target.value)}><option value="">First team</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select><span>VS</span><select value={secondTeamId} onChange={(event) => setSecondTeamId(event.target.value)}><option value="">Second team</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></div></header>{headToHead ? <div className="analytics-h2h-result"><div><b>{headToHead.first_team_wins}</b><span>{headToHead.first_team} wins</span></div><div><b>{headToHead.draws}</b><span>draws</span></div><div><b>{headToHead.second_team_wins}</b><span>{headToHead.second_team} wins</span></div><p>{headToHead.meetings ? `${headToHead.meetings} meetings in the ${headToHead.period} · Goals ${headToHead.first_team_goals}–${headToHead.second_team_goals}` : "No stored completed meetings in the last decade."}</p></div> : <p className="analytics-empty">Choose two teams to open their head-to-head record.</p>}</section>

            <section className="analytics-scorers"><header><div><span>Historical player leaderboard</span><h2>Top scorers · last 10 seasons</h2><p>Competition totals are imported from the football-data.org scorer feed and cached locally.</p></div><button type="button" onClick={loadDecadeScorers} disabled={loadingScorers}>{loadingScorers ? "Importing seasons…" : scorerData ? "Refresh scorer data" : "Load 10-season scorers"}</button></header>{scorerData ? <>{scorerData.coverage?.length ? <p className="analytics-scorer-coverage">Coverage: {scorerData.coverage.join(" · ")}</p> : null}{scorerData.scorers?.length ? <div className="analytics-scorer-grid">{scorerData.scorers.slice(0, 10).map((scorer, index) => <article key={`${scorer.player}-${index}`}><b>#{index + 1}</b>{scorer.crest ? <img src={scorer.crest} alt="" /> : <i /> }<section><strong>{scorer.player}</strong><small>{scorer.club || "Club unavailable"} · {scorer.seasons?.length || 0} seasons</small></section><aside><strong>{scorer.goals}</strong><small>goals</small><em>{scorer.assists} assists</em></aside></article>)}</div> : <p className="analytics-empty">{scorerData.message || "No scorer records were returned for the available seasons."}</p>}</> : <p className="analytics-empty">Load the selected competition's historical scorer data. The first import uses up to 10 API requests; later views use your database cache.</p>}</section>
            <section className="analytics-outlook"><header><div><span>2026/27 season outlook</span><h2>Projected finish from five-season league history</h2><p>Weighted historical points-per-game and goal difference, combined with current-season results as they arrive.</p></div><small>{seasonOutlook?.historical_seasons_used?.join(" / ") || "No historical data"}</small></header>{seasonOutlook?.forecast?.length ? <div className="analytics-outlook-table">{seasonOutlook.forecast.map((team) => <div key={team.team}><b>{team.projected_position}</b>{team.crest ? <img src={team.crest} alt="" /> : <i /> }<strong>{team.team}</strong><span>{team.projected_points} projected pts</span><small>{team.historical_ppg} historical PPG · {team.remaining_fixtures} fixtures left</small></div>)}</div> : <p className="analytics-empty">{seasonOutlook?.message || "Season outlook will appear when historical results are available."}</p>}</section>

            <section className="analytics-history"><header><div><span>Five-season club record</span><h2>Historical league finishes</h2><p>Open a club to inspect its stored completed season totals.</p></div></header><div>{seasonOutlook?.history?.map((team) => <details key={team.team}><summary>{team.crest ? <img src={team.crest} alt="" /> : null}<strong>{team.team}</strong><span>{team.seasons.length} recorded seasons</span></summary>{team.seasons.length ? <section>{team.seasons.map((season) => <p key={season.season}><b>{season.season}</b><span>{season.position}th · {season.points} pts</span><span>{season.won}W {season.draw}D {season.lost}L</span><span>{season.goals_for}–{season.goals_against} goals</span></p>)}</section> : <p className="analytics-empty">No completed season table is stored for this club in the selected competition.</p>}</details>)}</div></section>

            {seasonOutlook?.top_scorer_candidates?.length ? <section className="analytics-goal-race"><header><span>2026/27 goal-race projection</span><h2>Current squad candidates</h2></header>{seasonOutlook.top_scorer_candidates.slice(0, 5).map((player, index) => <p key={player.player}><b>#{index + 1} {player.player}</b><span>{player.club}</span><strong>{player.projected_goals} projected goals</strong></p>)}</section> : null}
        </>}
    </section></MainLayout>;
}

export default Analytics;
