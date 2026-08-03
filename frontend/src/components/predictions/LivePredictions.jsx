import PredictionCard from "./PredictionCard";
import PredictionHeader from "./PredictionHeader";
import usePredictions from "../../hooks/usePredictions";
import "./LivePredictions.css";

const LivePredictions = () => {
    const {
        predictions,
        loading,
        error,
    } = usePredictions();

    if (loading) {
        return (
            <section className="live-predictions">
                <div className="live-predictions-loading">
                    <p>Loading today's predictions...</p>
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="live-predictions">
                <div className="live-predictions-error">
                    <h3>Unable to load predictions</h3>

                    <p>{error}</p>
                </div>
            </section>
        );
    }

    return (
        <section className="live-predictions">
            <PredictionHeader />

            {predictions.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state-icon">
                        ⚽
                    </div>

                    <h3>No Matches Scheduled Today</h3>

                    <p>
                        There are currently no football matches available for
                        prediction today. Check back when new fixtures are
                        scheduled.
                    </p>
                </div>
            ) : (
                <div className="prediction-grid">
                    {predictions.map((prediction) => (
                        <PredictionCard
                            key={prediction.id}
                            prediction={prediction}
                        />
                    ))}
                </div>
            )}
        </section>
    );
};

export default LivePredictions;