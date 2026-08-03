import "./PredictionBar.css";

const PredictionBar = ({
    homeProbability = 0,
    drawProbability = 0,
    awayProbability = 0,
}) => {
    const home = Math.max(0, Math.min(homeProbability, 100));
    const draw = Math.max(0, Math.min(drawProbability, 100));
    const away = Math.max(0, Math.min(awayProbability, 100));

    return (
        <div className="prediction-bar">
            <div
                className="prediction-segment home"
                style={{ width: `${home}%` }}
                title={`Home Win: ${home.toFixed(1)}%`}
            />

            <div
                className="prediction-segment draw"
                style={{ width: `${draw}%` }}
                title={`Draw: ${draw.toFixed(1)}%`}
            />

            <div
                className="prediction-segment away"
                style={{ width: `${away}%` }}
                title={`Away Win: ${away.toFixed(1)}%`}
            />
        </div>
    );
};

export default PredictionBar;