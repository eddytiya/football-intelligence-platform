import useMatches from "../../hooks/useMatches";
import UpcomingMatchCard from "./UpcomingMatchCard";
import "./UpcomingMatches.css";

const UpcomingMatches = () => {

    const {
        matches,
        loading,
        error,
    } = useMatches(10);

    if (loading) {
        return (
            <section className="upcoming-matches">
                <h2>Upcoming Matches</h2>

                <p>Loading upcoming matches...</p>
            </section>
        );
    }

    if (error) {
        return (
            <section className="upcoming-matches">
                <h2>Upcoming Matches</h2>

                <p>{error.message}</p>
            </section>
        );
    }

    if (matches.length === 0) {
        return (
            <section className="upcoming-matches">
                <h2>Upcoming Matches</h2>

                <p>No upcoming matches found.</p>
            </section>
        );
    }

    return (
        <section className="upcoming-matches">

            <h2>Upcoming Matches</h2>

            <div className="upcoming-matches-grid">

                {matches.map((match) => (
                    <UpcomingMatchCard
                        key={match.id}
                        match={match}
                    />
                ))}

            </div>

        </section>
    );
};

export default UpcomingMatches;