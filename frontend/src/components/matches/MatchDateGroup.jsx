import MatchCard from "./MatchCard";
import { useEffect, useRef, useState } from "react";
import "./Matches.css";

function MatchDateGroup({ date, competitions, hideCompetitionHeading = false, autoShowPrediction = false }) {
    const groupRef = useRef(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setIsVisible(true);
                observer.disconnect();
            }
        }, { threshold: 0.08 });
        if (groupRef.current) observer.observe(groupRef.current);
        return () => observer.disconnect();
    }, []);

    return (
        <section ref={groupRef} className={`date-group scroll-reveal${isVisible ? " is-visible" : ""}`}>

            <h2 className="date-heading">

                {date}

            </h2>

            {competitions.map((competition) => (

                <div
                    key={competition.competition_id}
                    className="competition-group"
                >

                    {!hideCompetitionHeading && <div className="competition-heading">

                        <img
                            src={competition.competition_emblem}
                            alt={competition.competition_name}
                            className="competition-logo"
                        />

                        <h3>

                            {competition.competition_name}

                        </h3>

                        <span className="competition-match-count">
                            {competition.matches.length} {competition.matches.length === 1 ? "match" : "matches"}
                        </span>

                    </div>}

                    {competition.matches.map((match) => (

                        <MatchCard
                            key={match.id}
                            match={match}
                            autoShowPrediction={autoShowPrediction}
                        />

                    ))}

                </div>

            ))}

        </section>
    );

}

export default MatchDateGroup;
