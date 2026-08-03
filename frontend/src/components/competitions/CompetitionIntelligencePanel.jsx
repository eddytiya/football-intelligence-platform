import { useMemo, useState } from "react";

const badgeClass = (trend) => trend === "Improving" ? "is-improving" : trend === "Declining" ? "is-declining" : "is-stable";

function CompetitionIntelligencePanel({ intelligence }) {
    const [view, setView] = useState("projection");
    const contenders = useMemo(() => [...(intelligence?.table || [])].sort((a, b) => b.title_probability - a.title_probability).slice(0, 3), [intelligence]);

    if (!intelligence || intelligence.data_coverage === 0) return <section className="competition-ml-panel competition-ml-waiting"><div><span>Competition intelligence</span><h2>Simulation model warming up</h2><p>Attack, defence, form trends, upset alerts, and final-table probabilities start learning from the first synced result.</p></div><div className="competition-ml-orbits"><i /><i /><i /></div></section>;

    return <section className="competition-ml-panel">
        <header className="competition-ml-header"><div><span>Competition intelligence</span><h2>Season projection centre</h2><p>{intelligence.data_coverage} completed matches · {intelligence.simulations.toLocaleString()} simulated season run-ins</p></div><div className="competition-ml-tabs"><button className={view === "projection" ? "is-active" : ""} onClick={() => setView("projection")}>Projection</button><button className={view === "strength" ? "is-active" : ""} onClick={() => setView("strength")}>Team strength</button><button className={view === "upsets" ? "is-active" : ""} onClick={() => setView("upsets")}>Upsets</button></div></header>

        {view === "projection" && <><div className="competition-contenders">{contenders.map((team, index) => <article key={team.team}><b>#{index + 1}</b>{team.crest && <img src={team.crest} alt="" />}<div><strong>{team.team}</strong><span>Expected {team.expected_points} pts · rank {team.rank_range[0]}–{team.rank_range[1]}</span></div><em>{team.title_probability}%<small>title</small></em></article>)}</div><div className="competition-projection-table"><div className="competition-projection-labels"><span>Club</span><span>Exp pts</span><span>Exp rank</span><span>Top 4</span><span>Relegation</span></div>{intelligence.table.slice(0, 12).map((team) => <div className="competition-projection-row" key={team.team}><span>{team.crest && <img src={team.crest} alt="" />}{team.team}</span><b>{team.expected_points}</b><b>{team.expected_position}</b><i><u style={{ width: `${team.top_four_probability}%` }} /></i><strong className={team.relegation_probability > 35 ? "is-risk" : ""}>{team.relegation_probability}%</strong></div>)}</div></>}

        {view === "strength" && <div className="competition-strength-grid">{intelligence.table.slice(0, 12).map((team) => <article key={team.team}><div>{team.crest && <img src={team.crest} alt="" />}<strong>{team.team}</strong><span className={badgeClass(team.form_trend)}>{team.form_trend}</span></div><p><span>Attack</span><i><b style={{ width: `${Math.min(100, team.attack_rating * 50)}%` }} /></i><em>{team.attack_rating}</em></p><p><span>Defence</span><i><b style={{ width: `${Math.min(100, team.defence_rating * 50)}%` }} /></i><em>{team.defence_rating}</em></p><footer>{team.form.map((result, index) => <b className={`competition-form-${result}`} key={`${result}-${index}`}>{result}</b>)}</footer></article>)}</div>}

        {view === "upsets" && <div className="competition-upset-grid">{intelligence.upsets.length ? intelligence.upsets.map((match) => <article key={match.id}><span>Upset watch</span><h3>{match.home_team} <i>vs</i> {match.away_team}</h3><p><strong>{match.underdog}</strong> has a <b>{match.underdog_probability}%</b> win chance despite being the lower-ranked side.</p><footer><span>xG {match.expected_goals[0]} – {match.expected_goals[1]}</span><em>{new Date(match.utc_date).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</em></footer></article>) : <p className="competition-empty-fixtures">No qualifying upset opportunities yet. The detector activates once table positions differ.</p>}</div>}
    </section>;
}

export default CompetitionIntelligencePanel;
