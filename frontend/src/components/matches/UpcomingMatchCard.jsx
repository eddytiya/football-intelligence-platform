import "./UpcomingMatches.css";

const UpcomingMatchCard = ({ match }) => {
    return (
        <div className="match-card">

            <div className="competition-header">

                <img
                    src={match.competition_emblem}
                    alt={match.competition_name}
                    className="competition-logo"
                />

                <span>
                    {match.competition_name}
                </span>

            </div>

            <div className="teams-container">

                <div className="team">

                    <img
                        src={match.home_team_crest}
                        alt={match.home_team_name}
                        className="team-logo"
                    />

                    <h4>{match.home_team_name}</h4>

                </div>

                <div className="vs">

                    VS

                </div>

                <div className="team">

                    <img
                        src={match.away_team_crest}
                        alt={match.away_team_name}
                        className="team-logo"
                    />

                    <h4>{match.away_team_name}</h4>

                </div>

            </div>

            <div className="match-time">

                {new Date(match.utc_date).toLocaleString()}

            </div>

            <button className="predict-btn">

                Predict Match

            </button>

        </div>
    );
};

export default UpcomingMatchCard;