import "./Matches.css";

function MatchweekOverview({ competition, matchweek, maxMatchweek, fixtureCount, onPrevious, onNext, showPredictions, setShowPredictions, standings }) {
    return (
        <section className="matchweek-overview">
            <div className="matchweek-identity">
                {competition.emblem && <img src={competition.emblem} alt="" />}
                <div><span>Competition round</span><h2>{competition.name} · Matchweek {matchweek}</h2></div>
            </div>
            <div className="matchweek-progress">
                <span>Matchweek {matchweek} of {maxMatchweek}</span>
                <div><i style={{ width: `${(Number(matchweek) / maxMatchweek) * 100}%` }} /></div>
                <small>{fixtureCount} scheduled fixtures</small>
            </div>
            <div className="matchweek-actions">
                <button type="button" onClick={onPrevious} disabled={Number(matchweek) <= 1}>‹ Previous</button>
                <button type="button" onClick={onNext} disabled={Number(matchweek) >= maxMatchweek}>Next ›</button>
                <button type="button" className={showPredictions ? "is-active" : ""} onClick={() => setShowPredictions(!showPredictions)}>
                    {showPredictions ? "Hide predictions" : "Show predictions"}
                </button>
            </div>
            {standings?.leaders?.length > 0 && <div className="matchweek-standings">
                <span>Stored table · {standings.season}</span>
                <div><strong>Top 4</strong>{standings.leaders.map((team) => <small key={team.position}>{team.position}. {team.team} <b>{team.points}</b></small>)}</div>
                <div className="relegation"><strong>Bottom 3</strong>{standings.relegation_zone.map((team) => <small key={team.position}>{team.position}. {team.team} <b>{team.points}</b></small>)}</div>
            </div>}
        </section>
    );
}

export default MatchweekOverview;
