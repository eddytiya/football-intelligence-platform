import { useEffect, useState } from "react";
import predictionApi from "../api/predictionApi";

const usePredictions = () => {

    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchPredictions = async () => {
    try {
        setLoading(true);
        setError(null);

        const data = await predictionApi.getTodayPredictions();

        console.log("Predictions:", data);

        setPredictions(data);
    } catch (err) {
        console.error("Axios Error:", err);

        console.log("Response:", err.response);
        console.log("Message:", err.message);

        setError("Failed to load predictions.");
    } finally {
        setLoading(false);
    }
};

    useEffect(() => {

        fetchPredictions();

    }, []);

    return {
        predictions,
        loading,
        error,
        refresh: fetchPredictions,
    };

};

export default usePredictions;