import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getCompetitions } from "../api/competitionApi";
import { getPlayerPositions, getPlayers } from "../api/playerApi";
import "./Players.css";

const PLAYERS_PAGE_SIZE = 60;

function Players() {
    const [players, setPlayers] = useState([]);
    const [competitions, setCompetitions] = useState([]);
    const [positions, setPositions] = useState([]);
    const [search, setSearch] = useState("");
    const [competitionId, setCompetitionId] = useState("");
    const [position, setPosition] = useState("");
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(false);

    useEffect(() => {
        getCompetitions().then(setCompetitions).catch(() => setCompetitions([]));
        getPlayerPositions().then(setPositions).catch(() => setPositions([]));
    }, []);

    useEffect(() => {
        let active = true;
        const timer = setTimeout(() => {
            setLoading(true);
            getPlayers({ query: search, competitionId, position, limit: PLAYERS_PAGE_SIZE }).then((data) => {
                if (!active) return;
                setPlayers(data);
                setHasMore(data.length === PLAYERS_PAGE_SIZE);
            }).catch(() => active && setPlayers([])).finally(() => active && setLoading(false));
        }, 220);
        return () => { active = false; clearTimeout(timer); };
    }, [search, competitionId, position]);

    const loadMorePlayers = () => {
        setLoadingMore(true);
        getPlayers({ query: search, competitionId, position, limit: PLAYERS_PAGE_SIZE, offset: players.length }).then((data) => {
            setPlayers((current) => [...current, ...data]);
            setHasMore(data.length === PLAYERS_PAGE_SIZE);
        }).catch(() => setHasMore(false)).finally(() => setLoadingMore(false));
    };

    return <MainLayout><section className="players-page">
        <header className="players-hero">
            <div><span>Squad directory</span><h1>Players</h1><p>Every player currently stored from the top-5 leagues squad sync — search by name, or filter by league and position.</p></div>
            <div className="players-hero-stat"><b>{players.length}{hasMore ? "+" : ""}</b><span>players in this view</span></div>
        </header>

        <div className="players-controls">
            <label><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search a player, e.g. Bellingham..." /></label>
            <select value={competitionId} onChange={(event) => setCompetitionId(event.target.value)}>
                <option value="">All competitions</option>
                {competitions.map((competition) => <option key={competition.id} value={competition.id}>{competition.name}</option>)}
            </select>
            <select value={position} onChange={(event) => setPosition(event.target.value)}>
                <option value="">All positions</option>
                {positions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <button onClick={() => { setSearch(""); setCompetitionId(""); setPosition(""); }}>Reset</button>
        </div>

        {loading ? <FootballLoader label="Loading the player directory" /> : <>
            <div className="players-grid">
                {players.map((player) => <article className="player-card" key={player.id}>
                    <div className="player-card-shirt">{player.shirt_number ?? "—"}</div>
                    <div className="player-card-body">
                        <h2>{player.name}</h2>
                        <span>{player.position || "Position unavailable"}{player.nationality ? ` · ${player.nationality}` : ""}{player.age ? ` · ${player.age} yrs` : ""}</span>
                    </div>
                    {player.team_id ? <Link className="player-card-team" to={`/teams/${player.team_id}`}>
                        {player.team_crest ? <img src={player.team_crest} alt="" /> : <b>{player.team_name?.slice(0, 2)}</b>}
                        <span>{player.team_name}</span>
                    </Link> : <div className="player-card-team is-empty"><span>Club unavailable</span></div>}
                </article>)}
            </div>
            {!players.length && <div className="players-empty">No players match this search. Try a different name, league or position.</div>}
            {hasMore && <div className="players-load-more"><button type="button" onClick={loadMorePlayers} disabled={loadingMore}>{loadingMore ? "Loading…" : "Load more players"}</button></div>}
        </>}
    </section></MainLayout>;
}

export default Players;
