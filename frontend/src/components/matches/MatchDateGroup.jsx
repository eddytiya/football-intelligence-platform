import MatchCard from "./MatchCard";
import { useEffect, useId, useRef, useState } from "react";
import "./Matches.css";

function MatchDateGroup({ date, competitions, hideCompetitionHeading = false, autoShowPrediction = false }) {
    const groupRef = useRef(null);
    const [isVisible, setIsVisible] = useState(false);
    const [collapsedLeagues, setCollapsedLeagues] = useState({});
    const groupId = useId();

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

                        <h3 className="competition-toggle-heading">
                            <button
                                type="button"
                                className="competition-toggle"
                                aria-expanded={!collapsedLeagues[competition.competition_id]}
                                aria-controls={`${groupId}-${competition.competition_id}`}
                                aria-label={`${collapsedLeagues[competition.competition_id] ? "Expand" : "Collapse"} ${competition.competition_name}`}
                                onClick={() => setCollapsedLeagues((previous) => ({
                                    ...previous,
                                    [competition.competition_id]: !previous[competition.competition_id],
                                }))}
                            >
                                <span className="competition-toggle-name">{competition.competition_name}</span>
                                <span className="competition-match-count">
                            {competition.matches.length} {competition.matches.length === 1 ? "match" : "matches"}
                                </span>
                                <svg className="competition-toggle-chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <path d={collapsedLeagues[competition.competition_id] ? "m9 5 7 7-7 7" : "m5 9 7 7 7-7"} />
                                </svg>
                            </button>
                        </h3>

                    </div>}

                    <div id={`${groupId}-${competition.competition_id}`} hidden={!hideCompetitionHeading && Boolean(collapsedLeagues[competition.competition_id])}>
                    {competition.matches.map((match) => (

                        <MatchCard
                            key={match.id}
                            match={match}
                            broadcast
                            autoShowPrediction={autoShowPrediction}
                        />

                    ))}
                    </div>

                </div>

            ))}

        </section>
    );

}

export default MatchDateGroup;
