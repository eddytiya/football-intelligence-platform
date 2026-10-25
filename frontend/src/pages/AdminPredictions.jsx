import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import apiClient from "../api/apiClient";
import "./AdminPredictions.css";

const percent = (value) => value == null ? "—" : `${(value * 100).toFixed(1)}%`;
const dateKey = (offset) => { const d = new Date(); d.setDate(d.getDate() + offset); return d.toISOString().slice(0, 10); };

export default function AdminPredictions() {
    const [access, setAccess] = useState("checking");
    const [filters, setFilters] = useState({ start: dateKey(-7), end: dateKey(7), search: "", view: "all" });
    const [query, setQuery] = useState(filters);
    const [offset, setOffset] = useState(0);
    const [data, setData] = useState({ rows: [], total: 0 });
    const [performance, setPerformance] = useState(null);
    const [loading, setLoading] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [rowErrors, setRowErrors] = useState({});
    const [progress, setProgress] = useState("");
    const [detail, setDetail] = useState(null);
    const limit = 20;
    const replayResults = data.rows.filter((row) => row.kind === "walk_forward" && row.correct != null);
    const replayCorrect = replayResults.filter((row) => row.correct).length;

    useEffect(() => {
        let active = true;
        apiClient.get("/auth/me").then(({ data: user }) => active && setAccess(user.is_admin ? "admin" : "denied"))
            .catch(() => active && setAccess("denied"));
        return () => { active = false; };
    }, []);

    useEffect(() => {
        if (access !== "admin") return;
        let active = true;
        setLoading(true); setError(""); setRowErrors({}); setDetail(null);
        apiClient.get("/admin/predictions/matches", { params: { ...query, start: query.start || undefined, end: query.end || undefined, offset, limit } })
            .then(({ data: result }) => active && setData(result))
            .catch((e) => active && setError(e.response?.data?.detail || "Match review could not load. Apply the filters to retry."))
            .finally(() => active && setLoading(false));
        apiClient.get("/admin/predictions/performance").then(({ data: result }) => active && setPerformance(result)).catch(() => active && setPerformance(null));
        return () => { active = false; };
    }, [access, query, offset]);

    async function runReview(rows) {
        setBusy(true); setProgress("");
        for (const [index, row] of rows.entries()) {
            setProgress(`Reviewing ${index + 1} of ${rows.length} matches…`);
            setRowErrors((previous) => ({ ...previous, [row.id]: null }));
            try {
                const { data: result } = await apiClient.post(`/admin/predictions/match/${row.id}/review`);
                setData((previous) => ({ ...previous, rows: previous.rows.map((item) => item.id === row.id ? result : item) }));
                if (rows.length === 1) setDetail(result);
            } catch (e) {
                setRowErrors((previous) => ({ ...previous, [row.id]: e.response?.data?.detail || "Review failed. Try again." }));
            }
        }
        setProgress("Review complete. Matches without verified model history are marked below.");
        setBusy(false);
    }

    return <MainLayout><section className="admin-predictions">
        <header className="admin-review-header"><div><h1>Model performance review</h1><p>Compare past results with model outcomes, and inspect forecasts for upcoming matches.</p></div><Link to="/predictions">Prediction Centre</Link></header>
        {access === "checking" && <p role="status">Checking administrator access…</p>}
        {access === "denied" && <p role="alert">Administrator access is required. Sign in with your admin account to view this page.</p>}
        {access === "admin" && <>
            <section className="admin-review-performance" aria-label="Recorded forecast performance">
                <h2>Recorded pre-match performance</h2>
                <p>{performance ? <><strong>{percent(performance.accuracy)}</strong> outcome accuracy · {performance.correct} correct of {performance.settled} completed matches.</> : "Performance totals are unavailable."}</p>
                <p>Uses the first forecast saved on the server before kick-off for each match. {performance?.settled === 0 && "No saved forecasts have settled yet."}</p>
                <p>Historical backtests train only on results before the match’s calendar month and use form from earlier days. Backtest accuracy is shown separately from forecasts actually saved before kick-off.</p>
            </section>
            <form className="admin-review-filters" onSubmit={(event) => { event.preventDefault(); setOffset(0); setQuery({ ...filters }); }}>
                <fieldset disabled={busy}><legend>Find matches</legend>
                    <label>From (UTC)<input type="date" value={filters.start} onChange={(e) => setFilters({ ...filters, start: e.target.value })} /></label>
                    <label>To (UTC)<input type="date" value={filters.end} onChange={(e) => setFilters({ ...filters, end: e.target.value })} /></label>
                    <label>Matches<select value={filters.view} onChange={(e) => setFilters({ ...filters, view: e.target.value })}><option value="all">Past and future</option><option value="past">Past matches</option><option value="future">Future matches</option></select></label>
                    <label>Club<input type="search" placeholder="Search club name" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} /></label>
                    <button type="submit">Apply filters</button>
                    <button type="button" onClick={() => { const all = { start: "", end: "", search: "", view: "all" }; setFilters(all); setQuery(all); setOffset(0); }}>All dates</button>
                </fieldset>
            </form>
            {error && <p role="alert">{error}</p>}
            <div className="admin-review-actions"><p role="status">{loading ? "Loading matches…" : `${data.total.toLocaleString()} ${data.total === 1 ? "match" : "matches"} found`}</p><button type="button" disabled={busy || loading || Boolean(error) || !data.rows.some((row) => !row.forecast)} onClick={() => runReview(data.rows.filter((row) => !row.forecast))}>{busy ? "Reviewing…" : "Review this page"}</button></div>
            {progress && <p role="status">{progress}</p>}
            {replayResults.length > 0 && <p>Walk-forward backtest on this page: <strong>{replayCorrect} of {replayResults.length} correct ({percent(replayCorrect / replayResults.length)})</strong>. Training excludes this month and later results. Reconstructed backtests remain separate from recorded pre-match accuracy.</p>}
            {!loading && !error && <>
                {!data.rows.length ? <p>No matches found. Change the dates or club search.</p> : <div className="admin-review-table-scroll" tabIndex="0" role="region" aria-label="Match predictions and outcomes"><table className="admin-review-table"><thead><tr><th scope="col">Match</th><th scope="col">Prediction</th><th scope="col">Actual outcome</th><th scope="col">Comparison</th><th scope="col">Review</th></tr></thead><tbody>
                    {data.rows.map((row) => <tr key={row.id}><td><Link to={`/matches/${row.id}`}>{row.home_team} vs {row.away_team}</Link><small>{row.competition} · {new Date(/Z$|[+-]\d{2}:\d{2}$/.test(row.utc_date) ? row.utc_date : `${row.utc_date}Z`).toLocaleString()} · {row.status.replaceAll("_", " ")}</small></td>
                        <td>{row.forecast ? <>{row.forecast.predicted_outcome}<small>{row.kind === "pre_match" ? "Saved before kick-off" : "Walk-forward backtest"}</small></> : "Not reviewed"}</td>
                        <td>{row.actual_outcome ? <>{row.home_score}–{row.away_score}<small>{row.actual_outcome}</small></> : "Awaiting final result"}</td>
                        <td>{row.correct == null ? "—" : <span className={row.correct ? "admin-review-correct" : "admin-review-incorrect"}>{row.correct ? "Correct" : "Incorrect"}{row.kind === "walk_forward" && <small>Historical backtest</small>}</span>}</td>
                        <td>{row.forecast ? <button type="button" onClick={() => setDetail(row)}>Details</button> : <button type="button" disabled={busy} onClick={() => runReview([row])}>Review</button>}{rowErrors[row.id] && <small role="alert">{rowErrors[row.id]}</small>}</td></tr>)}
                </tbody></table></div>}
                <nav className="admin-review-pagination" aria-label="Review pages"><button type="button" disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Previous</button><span>{data.total ? `${offset + 1}–${Math.min(offset + limit, data.total)} of ${data.total.toLocaleString()}` : "0 matches"}</span><button type="button" disabled={busy || offset + limit >= data.total} onClick={() => setOffset(offset + limit)}>Next</button></nav>
            </>}
            {detail && <section className="admin-review-detail" aria-label="Forecast details"><div className="admin-review-actions"><h2>{detail.home_team} vs {detail.away_team}</h2><button type="button" onClick={() => setDetail(null)}>Close details</button></div><p>{detail.forecast.review_note || (detail.kind === "pre_match" ? "Saved before kick-off." : "Walk-forward backtest; reported separately from recorded accuracy.")}</p><dl><dt>Home win</dt><dd>{percent(detail.forecast.home_win_probability)}</dd><dt>Draw</dt><dd>{percent(detail.forecast.draw_probability)}</dd><dt>Away win</dt><dd>{percent(detail.forecast.away_win_probability)}</dd><dt>Likely score</dt><dd>{detail.forecast.score_prediction?.most_likely_score?.score || "Unavailable"}</dd><dt>Model</dt><dd>{detail.forecast.model_version}</dd><dt>Training through</dt><dd>{detail.forecast.training_data_through}</dd><dt>History through</dt><dd>{detail.forecast.history_through}</dd><dt>Generated</dt><dd>{new Date(detail.generated_at).toLocaleString()}</dd></dl></section>}
        </>}
    </section></MainLayout>;
}
