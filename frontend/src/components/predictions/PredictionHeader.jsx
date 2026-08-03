import "./PredictionHeader.css";

const PredictionHeader = () => {
    return (
        <div className="prediction-header">
            <div className="prediction-header-content">
                <h2>Today's Predictions</h2>

                <p>
                    AI-powered football match predictions for today's fixtures.
                </p>
            </div>

            <div className="prediction-header-badge">
                AI Powered
            </div>
        </div>
    );
};

export default PredictionHeader;