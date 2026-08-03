import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getCompetitions } from "../api/competitionApi";
import "./Competitions.css";

function Competitions() {
    const [competitions, setCompetitions] = useState([]);
    const [search, setSearch] = useState("");
    const [area, setArea] = useState("all");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getCompetitions().then(setCompetitions).catch(() => setCompetitions([])).finally(() => setLoading(false));
    }, []);

    const areas = useMemo(() => [...new Set(competitions.map((competition) => competition.area_name).filter(Boolean))].sort(), [competitions]);
    const visibleCompetitions = competitions.filter((competition) =>
        (area === "all" || competition.area_name === area)
        && `${competition.name} ${competition.area_name} ${competition.code}`.toLowerCase().includes(search.toLowerCase()),
    );

    return (
        <MainLayout>
            <section className="competitions-page">
                <header className="competitions-hero">
                    <div><span className="section-eyebrow">Football directory</span><h1>Competitions</h1><p>Explore leagues, cups, fixtures, and matchweek coverage from around the world.</p></div>
                    <div className="competition-hero-stat"><strong>{competitions.length}</strong><span>competitions tracked</span></div>
                </header>

                <div className="competition-controls">
                    <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search competition or country..." />
                    <select value={area} onChange={(event) => setArea(event.target.value)}><option value="all">All areas</option>{areas.map((item) => <option key={item} value={item}>{item}</option>)}</select>
                    <span>{visibleCompetitions.length} results</span>
                </div>

                {loading ? <FootballLoader label="Loading competitions" /> : (
                    <div className="competition-grid">
                        {visibleCompetitions.map((competition) => (
                            <article className="competition-card" key={competition.id}>
                                <div className="competition-card-top">
                                    <div className="competition-emblem-wrap">{competition.emblem ? <img src={competition.emblem} alt="" /> : <span>{competition.code}</span>}</div>
                                    <span className="competition-type">{competition.type || "Competition"}</span>
                                </div>
                                <div className="competition-card-title"><span>{competition.area_name}</span><h2>{competition.name}</h2></div>
                                <div className="competition-stats"><div><strong>{competition.scheduled_match_count}</strong><span>scheduled</span></div><div><strong>{competition.match_count}</strong><span>fixtures</span></div><div><strong>{competition.seasons_available || "—"}</strong><span>seasons</span></div></div>
                                <Link className="competition-card-link" to={`/competitions/${competition.id}`}>View fixtures <b>→</b></Link>
                            </article>
                        ))}
                    </div>
                )}
                {!loading && visibleCompetitions.length === 0 && <div className="competition-empty">No competitions match that search.</div>}
            </section>
        </MainLayout>
    );
}

export default Competitions;
