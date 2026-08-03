import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboardSummary } from "../api/dashboardApi";
import { getNextMatch } from "../api/matchApi";
import "./Landing.css";

const formatKickoff = (value) => value ? new Date(value).toLocaleString(undefined, {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
}) : "Kick-off to be confirmed";

function Landing() {
    const [summary, setSummary] = useState(null);
    const [featured, setFeatured] = useState(null);

    useEffect(() => {
        let active = true;
        getDashboardSummary().then((data) => active && setSummary(data)).catch(() => {});
        getNextMatch().then((data) => active && setFeatured(data)).catch(() => {});
        return () => { active = false; };
    }, []);

    return <main className="landing-page">
        <header className="landing-topbar">
            <Link className="landing-brand" to="/"><b>FI</b><span>Football Intelligence Platform<small>Predict · Analyse · Win</small></span></Link>
            <nav>
                <Link className="landing-signin" to="/login">Sign in</Link>
                <Link className="landing-signup" to="/register">Create free account</Link>
            </nav>
        </header>

        <section className="landing-hero">
            <div className="landing-hero-copy">
                <span className="landing-kicker">Matchday access</span>
                <h1>Every fixture.<br />One home.</h1>
                <p>Follow clubs, explore data-driven forecasts, and keep the football world at your fingertips — built from real stored results, not guesswork.</p>
                <div className="landing-hero-actions">
                    <Link to="/register" className="landing-primary">Create free account <b>→</b></Link>
                    <Link to="/login" className="landing-secondary">Sign in</Link>
                </div>
            </div>

            <aside className="landing-track-record">
                <span className="landing-track-kicker">Track record</span>
                {summary ? <>
                    <div className="landing-stat-grid">
                        <div><strong>{summary.accuracy != null ? `${(summary.accuracy * 100).toFixed(1)}%` : "—"}</strong><span>overall accuracy</span></div>
                        <div><strong>{summary.total_predictions ?? "—"}</strong><span>predictions made</span></div>
                    </div>
                    <p className="landing-track-note">A forecast is not a guarantee — accuracy reflects every prediction we've scored so far, updated as results come in.</p>
                </> : <p className="landing-track-note">Loading current model accuracy…</p>}
            </aside>
        </section>

        {featured && <section className="landing-featured">
            <span className="landing-kicker">Next up</span>
            <article className="landing-featured-match">
                <header><span>{featured.competition_name || "Fixture"}</span><b>{formatKickoff(featured.utc_date)}</b></header>
                <div className="landing-featured-teams">
                    <section>{featured.home_team_crest ? <img src={featured.home_team_crest} alt="" /> : null}<strong>{featured.home_team_name}</strong></section>
                    <b className="landing-versus">VS</b>
                    <section>{featured.away_team_crest ? <img src={featured.away_team_crest} alt="" /> : null}<strong>{featured.away_team_name}</strong></section>
                </div>
                <footer>Sign up to see the full forecast, expected goals, and model reasoning for this match.</footer>
            </article>
        </section>}

        <section className="landing-cta">
            <div>
                <h2>Build your matchday hub.</h2>
                <p>Save favourite clubs, track a fixture watchlist, and keep a saved history of every forecast — free.</p>
            </div>
            <Link to="/register" className="landing-primary">Create free account <b>→</b></Link>
        </section>
    </main>;
}

export default Landing;
