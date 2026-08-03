import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import predictionApi from "../../api/predictionApi";
import { getCompetitionSeasonOutlook } from "../../api/matchApi";
import { getTeamComparison } from "../../api/teamApi";
import { removeWatchlist, saveWatchlist } from "../../api/accountApi";
import "./Matches.css";

function AnimatedNumber({ value, decimals = 1, suffix = "" }) {
    const [displayValue, setDisplayValue] = useState(0);

    useEffect(() => {
        const start = performance.now();
        const startValue = displayValue;
        const target = Number(value) || 0;
        let frame;
        const animate = (time) => {
            const progress = Math.min((time - start) / 450, 1);
            setDisplayValue(startValue + (target - startValue) * (1 - (1 - progress) ** 3));
            if (progress < 1) frame = requestAnimationFrame(animate);
        };
        frame = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frame);
    }, [value]);

    return <>{displayValue.toFixed(decimals)}{suffix}</>;
}

function MatchCountdown({ utcDate, isFinished, isLive }) {
    const [remaining, setRemaining] = useState("");

    useEffect(() => {
        const update = () => {
            const difference = new Date(utcDate).getTime() - Date.now();
            if (difference <= 0) return setRemaining("");
            const hours = Math.floor(difference / 3_600_000);
            const days = Math.floor(hours / 24);
            setRemaining(days > 0 ? `Starts in ${days}d ${hours % 24}h` : `Starts in ${hours}h`);
        };
        update();
        const timer = window.setInterval(update, 60_000);
        return () => window.clearInterval(timer);
    }, [utcDate]);

    if (isFinished || isLive || !remaining) return null;
    return <span className="match-countdown">{remaining}</span>;
}

function TeamIdentity({ id, crest, name, away = false }) {
    const content = away
        ? <><span>{name}</span><img src={crest} alt="" /></>
        : <><img src={crest} alt="" /><span>{name}</span></>;
    if (!id) return <div className={`match-card-team${away ? " match-card-away" : " match-card-home"}`}>{content}</div>;
    return <Link className={`match-card-team match-team-link${away ? " match-card-away" : " match-card-home"}`} to={`/teams/${id}`} title={`Open ${name} team profile`}>{content}</Link>;
}

const poisson = (goals, expected) => (Math.exp(-expected) * (expected ** goals)) / factorial(goals);
const factorial = (number) => number <= 1 ? 1 : number * factorial(number - 1);
const percentage = (value) => `${(value * 100).toFixed(1)}%`;

function PredictionExtras({ match, prediction }) {
    const score = prediction.score_prediction;
    const homeExpected = score?.home_expected_goals || 0;
    const awayExpected = score?.away_expected_goals || 0;
    const scoreGrid = Array.from({ length: 5 }, (_, home) => Array.from({ length: 5 }, (_, away) => ({ home, away, probability: poisson(home, homeExpected) * poisson(away, awayExpected) })));
    const totalGoalProbability = (minimum) => Array.from({ length: 9 }, (_, total) => total).filter((total) => total >= minimum).reduce((sum, total) => sum + Array.from({ length: total + 1 }, (_, home) => poisson(home, homeExpected) * poisson(total - home, awayExpected)).reduce((inner, value) => inner + value, 0), 0);
    const btts = (1 - poisson(0, homeExpected)) * (1 - poisson(0, awayExpected));
    const form = prediction.form_insights;
    const formPoints = (entry) => (entry?.wins || 0) * 3 + (entry?.draws || 0);
    const formOutcome = !form ? "Awaiting form data" : formPoints(form.home) === formPoints(form.away) ? "Draw signal" : formPoints(form.home) > formPoints(form.away) ? match.home_team_name : match.away_team_name;
    const sharePrediction = async () => {
        const text = `${match.home_team_name} vs ${match.away_team_name}: ${prediction.predicted_outcome}, likely score ${score?.most_likely_score?.score || "N/A"}.`;
        if (navigator.share) await navigator.share({ title: "Football Intelligence prediction", text });
        else await navigator.clipboard.writeText(text);
    };

    const ensemble = prediction.ensemble;
    const similarMatches = prediction.similar_matches || [];

    return <div className="prediction-extras">
        <section className="prediction-market-panel"><header><span>Goal markets</span><small>Derived from expected goals</small></header><div><article><b>{percentage(btts)}</b><span>Both teams score</span></article><article><b>{percentage(totalGoalProbability(2))}</b><span>Over 1.5 goals</span></article><article><b>{percentage(totalGoalProbability(3))}</b><span>Over 2.5 goals</span></article><article><b>{percentage(poisson(0, awayExpected))}</b><span>{match.home_team_name} clean sheet</span></article><article><b>{percentage(poisson(0, homeExpected))}</b><span>{match.away_team_name} clean sheet</span></article></div></section>
        <section className="prediction-score-grid"><header><span>Exact score grid</span><small>Probability · 0–4 goals</small></header><div className="score-grid-table"><i>H\A</i>{[0, 1, 2, 3, 4].map((away) => <i key={`away-${away}`}>{away}</i>)}{scoreGrid.flatMap((row, home) => [<i key={`home-${home}`}>{home}</i>, ...row.map((cell) => <b key={`${cell.home}-${cell.away}`} className={cell.probability > 0.1 ? "is-likely" : ""}>{percentage(cell.probability)}</b>)])}</div></section>
        <section className="prediction-context-panel"><header><span>Match context</span><small>Fixture and squad data</small></header><div><article><b>{match.competition_name}</b><span>{match.match_week ? `Matchweek ${match.match_week}` : "Competition fixture"}</span></article><article><b>{new Date(match.utc_date).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })}</b><span>{new Date(match.utc_date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} local kick-off</span></article><article><b>Squad records available</b><span>Injury and confirmed starting-XI feeds are not connected yet.</span></article></div></section>
        <section className="prediction-consensus-panel"><header><span>Prediction comparison</span><small>Independent model signals</small></header><div><article><b>{prediction.predicted_outcome}</b><span>Historical ML</span></article><article><b>{formOutcome}</b><span>Recent five-match form</span></article><article><b>{prediction.team_comparison?.home.attack > prediction.team_comparison?.away.attack ? match.home_team_name : match.away_team_name}</b><span>Attack-strength signal</span></article></div><p>Signals are shown side-by-side to explain agreement or disagreement; they are not separate betting models.</p></section>
        {ensemble && <section className="prediction-ensemble-panel"><header><span>Forecast ensemble</span><small>{ensemble.name}</small></header><strong>{ensemble.agreement}</strong><div>{Object.entries(ensemble.signals || {}).map(([name, values]) => <article key={name}><b>{name.replaceAll("_", " ")}</b><span>{match.home_team_name} {percentage(values.home)} · Draw {percentage(values.draw)} · {match.away_team_name} {percentage(values.away)}</span></article>)}</div></section>}
        <section className="prediction-similar-panel"><header><span>Similar historical fixtures</span><small>Same league · pre-match profile</small></header>{similarMatches.length ? <div>{similarMatches.map((fixture) => <article key={`${fixture.date}-${fixture.home_team}-${fixture.away_team}`}><small>{new Date(fixture.date).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })} · {Math.round(fixture.similarity * 100)}% similar</small><b>{fixture.home_team} {fixture.score} {fixture.away_team}</b></article>)}</div> : <p>Similar-fixture history will appear after the refreshed historical artifact is trained.</p>}</section>
        <section className="prediction-coverage-panel"><header><span>Forecast coverage</span><small>What the model can verify</small></header><p>{prediction.data_coverage?.basis || "Historical form and fixture context."}</p><div><span>Team mapping: {percentage(prediction.data_coverage?.historical_team_mapping || 0)}</span><span>Player availability: {prediction.data_coverage?.player_availability === "not_connected" ? "not connected" : "available"}</span><span>Venue/referee: {prediction.data_coverage?.venue_and_referee === "not_connected" ? "not connected" : "available"}</span></div></section>
        <div className="prediction-extra-actions"><button type="button" onClick={sharePrediction}>Share prediction</button><small>Saving happens automatically while this prediction is open.</small></div>
    </div>;
}

function MatchCard({ match, autoShowPrediction = false, onPredictionSaved }) {
    const [prediction, setPrediction] = useState(null);
    const [predictionError, setPredictionError] = useState(null);
    const [isLoadingPrediction, setIsLoadingPrediction] = useState(false);
    const [showDetails, setShowDetails] = useState(false);
    const [headToHead, setHeadToHead] = useState(null);
    const [leagueOutlook, setLeagueOutlook] = useState(null);
    const [isFavourite, setIsFavourite] = useState(() =>
        JSON.parse(localStorage.getItem("favouriteMatchIds") || "[]").includes(match.id),
    );
    const [favouriteBurst, setFavouriteBurst] = useState(false);
    const previousScore = useRef(`${match.home_score}-${match.away_score}`);
    const [scoreChanged, setScoreChanged] = useState(false);
    const isFinished = match.status === "FINISHED";
    const isLive = ["LIVE", "IN_PLAY", "PAUSED"].includes(match.status);

    useEffect(() => {
        const currentScore = `${match.home_score}-${match.away_score}`;
        if (previousScore.current !== currentScore) {
            setScoreChanged(true);
            window.setTimeout(() => setScoreChanged(false), 850);
        }
        previousScore.current = currentScore;
    }, [match.home_score, match.away_score]);

    useEffect(() => {
        if (!prediction || !match.home_team_id || !match.away_team_id) { setHeadToHead(null); return undefined; }
        let active = true;
        getTeamComparison(match.home_team_id, match.away_team_id).then((data) => active && setHeadToHead(data)).catch(() => active && setHeadToHead(null));
        return () => { active = false; };
    }, [prediction, match.home_team_id, match.away_team_id]);

    useEffect(() => {
        if (!prediction || !match.competition_id) { setLeagueOutlook(null); return undefined; }
        let active = true;
        getCompetitionSeasonOutlook(match.competition_id).then((data) => active && setLeagueOutlook(data)).catch(() => active && setLeagueOutlook(null));
        return () => { active = false; };
    }, [prediction, match.competition_id]);
    const kickoff = new Date(match.utc_date).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
    });
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone?.replace("_", " ") || "local time";
    const statusLabel = isFinished ? "Full time" : isLive ? "Live" : "Upcoming";
    const predictedOutcomeLabel = prediction?.predicted_outcome === "Home Win"
        ? match.home_team_name
        : prediction?.predicted_outcome === "Away Win"
            ? match.away_team_name
            : prediction?.predicted_outcome;

    const showPrediction = async () => {
        if (prediction) {
            setPrediction(null);
            return;
        }

        try {
            setIsLoadingPrediction(true);
            setPredictionError(null);
            const result = await predictionApi.getHistoricalPrediction(match.id);
            setPrediction(result);
            const history = JSON.parse(localStorage.getItem("prediction-history") || "[]").filter((item) => item.match_id !== match.id);
            history.unshift({ match_id: match.id, home_team: match.home_team_name, away_team: match.away_team_name, utc_date: match.utc_date, predicted_outcome: result.predicted_outcome, likely_score: result.score_prediction?.most_likely_score?.score || null, saved_at: new Date().toISOString() });
            localStorage.setItem("prediction-history", JSON.stringify(history.slice(0, 30)));
            onPredictionSaved?.();
        } catch (error) {
            setPredictionError(error.response?.data?.detail || "Prediction is unavailable right now.");
        } finally {
            setIsLoadingPrediction(false);
        }
    };

    useEffect(() => {
        if (autoShowPrediction && !prediction && !isLoadingPrediction) showPrediction();
    // Trigger only when the parent explicitly toggles bulk prediction display.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [autoShowPrediction]);

    const toggleFavourite = () => {
        const favourites = new Set(JSON.parse(localStorage.getItem("favouriteMatchIds") || "[]"));
        if (favourites.has(match.id)) favourites.delete(match.id);
        else favourites.add(match.id);
        localStorage.setItem("favouriteMatchIds", JSON.stringify([...favourites]));
        // Keep the fast local interaction while also persisting the user's
        // watchlist when they are signed in. Offline/public use still works.
        if (favourites.has(match.id)) saveWatchlist(match.id).catch(() => null);
        else removeWatchlist(match.id).catch(() => null);
        setIsFavourite(favourites.has(match.id));
        if (favourites.has(match.id)) {
            setFavouriteBurst(true);
            window.setTimeout(() => setFavouriteBurst(false), 500);
        }
    };

    const formChips = (form) => [...(form || "")].map((result, index) => (
        <span className={`form-chip form-${result.toLowerCase()}`} key={`${result}-${index}`}>{result}</span>
    ));

    return (
        <article className={`match-card${prediction ? " has-prediction" : ""}${prediction?.confidence?.level === "High" ? " high-confidence" : ""}`}>
            <div className="match-card-status">
                <span className={`match-status-pill${isLive ? " is-live" : ""}`}>
                    {isLive && <span className="live-indicator" />}
                    {statusLabel}
                </span>
                {match.match_week && <span className="matchweek-pill">MW {match.match_week}</span>}
            </div>
            <button type="button" className={`match-favourite-btn${isFavourite ? " is-favourite" : ""}${favouriteBurst ? " favourite-burst" : ""}`} onClick={toggleFavourite} aria-label={isFavourite ? "Remove from favourites" : "Add to favourites"}>
                {isFavourite ? "★" : "☆"}
            </button>

            <TeamIdentity id={match.home_team_id} crest={match.home_team_crest} name={match.home_team_name} />

            <div className="match-card-score">
                <strong className={scoreChanged ? "score-updated" : ""}>{isFinished ? `${match.home_score} – ${match.away_score}` : kickoff}</strong>
                <span>{isFinished ? "Final score" : `Kick-off · ${timezone}`}</span>
                <MatchCountdown utcDate={match.utc_date} isFinished={isFinished} isLive={isLive} />
                {!isFinished && (
                    <button type="button" className="match-prediction-btn" onClick={showPrediction} disabled={isLoadingPrediction}>
                        {isLoadingPrediction ? "Loading…" : prediction ? "Hide prediction" : "✦ Prediction →"}
                    </button>
                )}
                <Link className="match-details-btn" to={`/matches/${match.id}`}>Match centre</Link>
                <button type="button" className="match-details-btn" onClick={() => setShowDetails((shown) => !shown)}>
                    {showDetails ? "Hide details" : "Quick details"}
                </button>
            </div>

            <TeamIdentity id={match.away_team_id} crest={match.away_team_crest} name={match.away_team_name} away />

            {prediction && (
                <div className="match-prediction-panel">
                    <div className="prediction-panel-heading">
                        <span className="prediction-panel-label">Historical ML prediction</span>
                        <span className={`prediction-confidence confidence-${prediction.confidence?.level?.toLowerCase() || "low"}`}>
                            {prediction.confidence?.level || "Low"} confidence
                        </span>
                    </div>
                    <strong className="prediction-outcome">{predictedOutcomeLabel}</strong>
                    <div className="prediction-probabilities">
                        <span><b>{match.home_team_name}</b> <AnimatedNumber value={prediction.home_win_probability * 100} suffix="%" /></span>
                        <span><b>Draw</b> <AnimatedNumber value={prediction.draw_probability * 100} suffix="%" /></span>
                        <span><b>{match.away_team_name}</b> <AnimatedNumber value={prediction.away_win_probability * 100} suffix="%" /></span>
                    </div>
                    <div className="prediction-probability-bar" aria-label="Match outcome probabilities">
                        <span className="probability-home" style={{ width: `${prediction.home_win_probability * 100}%` }} />
                        <span className="probability-draw" style={{ width: `${prediction.draw_probability * 100}%` }} />
                        <span className="probability-away" style={{ width: `${prediction.away_win_probability * 100}%` }} />
                    </div>
                    {prediction.score_prediction && (
                        <div className="score-prediction">
                            <div>
                                <span>Expected goals</span>
                                <strong>{match.home_team_name} <AnimatedNumber value={prediction.score_prediction.home_expected_goals} decimals={2} /> <em>–</em> <AnimatedNumber value={prediction.score_prediction.away_expected_goals} decimals={2} /> {match.away_team_name}</strong>
                            </div>
                            <div>
                                <span>Most likely score</span>
                                <strong>{prediction.score_prediction.most_likely_score.score}</strong>
                                <small><AnimatedNumber value={prediction.score_prediction.most_likely_score.probability * 100} suffix="%" /></small>
                            </div>
                            <div className="likely-scorelines">
                                <span>Other likely scores</span>
                                <small>{prediction.score_prediction.likely_scorelines.slice(1).map((scoreline) => `${scoreline.score} (${(scoreline.probability * 100).toFixed(1)}%)`).join(" · ")}</small>
                            </div>
                        </div>
                    )}
                    {prediction.form_insights && (
                        <div className="prediction-insights">
                            <div className="form-insight">
                                <span>{match.home_team_name} · last {prediction.form_insights.home.matches}</span>
                                <strong>{prediction.form_insights.home.form || "No recent data"}</strong>
                                <div className="form-chips">{formChips(prediction.form_insights.home.form)}</div>
                                <small>{prediction.form_insights.home.wins}W {prediction.form_insights.home.draws}D {prediction.form_insights.home.losses}L · {prediction.form_insights.home.goals_scored} GF · {prediction.form_insights.home.goals_conceded} GA · {prediction.form_insights.home.clean_sheets} CS</small>
                            </div>
                            <div className="prediction-explanations">
                                <span>Why the model leans this way</span>
                                {prediction.explanations?.map((explanation) => <small key={explanation}>• {explanation}</small>)}
                            </div>
                            <div className="form-insight form-insight-away">
                                <span>{match.away_team_name} · last {prediction.form_insights.away.matches}</span>
                                <strong>{prediction.form_insights.away.form || "No recent data"}</strong>
                                <div className="form-chips form-chips-away">{formChips(prediction.form_insights.away.form)}</div>
                                <small>{prediction.form_insights.away.wins}W {prediction.form_insights.away.draws}D {prediction.form_insights.away.losses}L · {prediction.form_insights.away.goals_scored} GF · {prediction.form_insights.away.goals_conceded} GA · {prediction.form_insights.away.clean_sheets} CS</small>
                            </div>
                        </div>
                    )}
                    {prediction.team_comparison && (
                        <div className="team-comparison">
                            <span className="comparison-title">Team comparison</span>
                            {["attack", "defence", "form_points", "rest_days"].map((metric) => {
                                const homeValue = prediction.team_comparison.home[metric];
                                const awayValue = prediction.team_comparison.away[metric];
                                const max = Math.max(homeValue, awayValue, 1);
                                return <div className="comparison-row" key={metric}>
                                    <strong>{homeValue}</strong><div className="comparison-bars"><i style={{ width: `${(homeValue / max) * 100}%` }} /><span>{metric === "form_points" ? "Form" : metric === "rest_days" ? "Rest days" : metric[0].toUpperCase() + metric.slice(1)}</span><i className="comparison-away-bar" style={{ width: `${(awayValue / max) * 100}%` }} /></div><strong>{awayValue}</strong>
                                </div>;
                            })}
                            {prediction.team_comparison.head_to_head_matches > 0 && <small>{prediction.team_comparison.head_to_head_matches} recorded head-to-head matches</small>}
                        </div>
                    )}
                    {headToHead && (
                        <section className="prediction-head-to-head">
                            <header><div><span>Head to head · {headToHead.period}</span><strong>{headToHead.meetings ? `${headToHead.meetings} completed meetings` : "No completed meetings found"}</strong></div>{headToHead.meetings > 0 && <small>Goals: {headToHead.first_team_goals} – {headToHead.second_team_goals}</small>}</header>
                            {headToHead.meetings > 0 ? <><div className="prediction-h2h-record"><div><b>{headToHead.first_team_wins}</b><span>{match.home_team_name} wins</span></div><div><b>{headToHead.draws}</b><span>Draws</span></div><div><b>{headToHead.second_team_wins}</b><span>{match.away_team_name} wins</span></div></div><div className="prediction-h2h-meetings">{headToHead.recent_meetings.map((meeting) => <article key={meeting.id}><small>{meeting.competition || "Competition"} · {new Date(meeting.utc_date).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</small><strong>{meeting.home_team} <b>{meeting.home_score}–{meeting.away_score}</b> {meeting.away_team}</strong></article>)}</div></> : <p>These teams have not played each other in the stored results from the last decade.</p>}
                        </section>
                    )}
                    {leagueOutlook?.forecast?.length > 0 && (
                        <section className="prediction-league-outlook">
                            <header><div><span>{leagueOutlook.season} season forecast</span><strong>Predicted {match.competition_name} table</strong></div><small>Five-season model</small></header>
                            <div>{leagueOutlook.forecast.map((team) => <article key={team.team} className={team.team === match.home_team_name || team.team === match.away_team_name ? "is-playing" : ""}><b>{team.projected_position}</b>{team.crest ? <img src={team.crest} alt="" /> : <i /> }<strong>{team.team}</strong><span>{team.projected_points} pts</span><small>{team.historical_ppg} PPG</small></article>)}</div>
                        </section>
                    )}
                    <PredictionExtras match={match} prediction={prediction} />
                </div>
            )}

            {predictionError && <p className="match-prediction-error">{predictionError}</p>}
            {showDetails && (
                <div className="match-details-panel">
                    <span><b>Competition</b>{match.competition_name}</span>
                    <span><b>Kick-off</b>{new Date(match.utc_date).toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                    <span><b>Status</b>{statusLabel}</span>
                </div>
            )}
        </article>
    );
}

export default MatchCard;
