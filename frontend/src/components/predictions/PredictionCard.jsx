import PredictionBar from "./PredictionBar";
import "./PredictionCard.css";

const PredictionCard = ({ prediction }) => {
    const matchDate = new Date(
        prediction.utc_date
    ).toLocaleString();

    return (
        <div className="prediction-card">
            <div className="competition-header">
                <div className="competition-info">
                    {prediction.competition_logo && (
                        <img
                            src={prediction.competition_logo}
                            alt={prediction.competition}
                            className="competition-logo"
                        />
                    )}

                    <span>{prediction.competition}</span>
                </div>

                <span className="match-date">
                    {matchDate}
                </span>
            </div>

            <div className="teams">
                <div className="team">
                    {prediction.home_team_logo && (
                        <img
                            src={prediction.home_team_logo}
                            alt={prediction.home_team}
                            className="team-logo"
                        />
                    )}

                    <p>{prediction.home_team}</p>
                </div>

                <div className="prediction-result">
                    <span className="prediction-badge">
                        {prediction.prediction}
                    </span>
                </div>

                <div className="team">
                    {prediction.away_team_logo && (
                        <img
                            src={prediction.away_team_logo}
                            alt={prediction.away_team}
                            className="team-logo"
                        />
                    )}

                    <p>{prediction.away_team}</p>
                </div>
            </div>

            <PredictionBar
                homeProbability={prediction.home_probability}
                drawProbability={prediction.draw_probability}
                awayProbability={prediction.away_probability}
            />

            <div className="probabilities">
                <span>
                    🏠 {prediction.home_probability.toFixed(1)}%
                </span>

                <span>
                    🤝 {prediction.draw_probability.toFixed(1)}%
                </span>

                <span>
                    ✈️ {prediction.away_probability.toFixed(1)}%
                </span>
            </div>
        </div>
    );
};

export default PredictionCard;