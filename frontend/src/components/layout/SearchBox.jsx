import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getTeams } from "../../api/teamApi";
import { searchMatchesByTeam } from "../../api/matchApi";
import "./SearchBox.css";
import { FiSearch } from "react-icons/fi";

function SearchBox() {
    const navigate = useNavigate();
    const containerRef = useRef(null);
    const [term, setTerm] = useState("");
    const [teams, setTeams] = useState([]);
    const [matches, setMatches] = useState([]);
    const [open, setOpen] = useState(false);
    const [searching, setSearching] = useState(false);

    useEffect(() => {
        const query = term.trim();
        if (query.length < 2) { setTeams([]); setMatches([]); setSearching(false); return undefined; }
        let active = true;
        setSearching(true);
        const timer = setTimeout(() => {
            Promise.all([
                getTeams({ query, limit: 5 }).catch(() => []),
                searchMatchesByTeam(query).catch(() => []),
            ]).then(([teamResults, matchResults]) => {
                if (!active) return;
                setTeams(teamResults.slice(0, 5));
                setMatches(matchResults.slice(0, 5));
            }).finally(() => active && setSearching(false));
        }, 300);
        return () => { active = false; clearTimeout(timer); };
    }, [term]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) setOpen(false);
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const goTo = (path) => {
        setOpen(false);
        setTerm("");
        navigate(path);
    };

    const hasResults = teams.length > 0 || matches.length > 0;
    const showDropdown = open && term.trim().length >= 2;

    return <div className="navbar-search" ref={containerRef}>
        <span className="navbar-search-icon"><FiSearch /></span>
        <input
            value={term}
            onChange={(event) => { setTerm(event.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); }}
            placeholder="Search clubs or fixtures…"
            aria-label="Search clubs or fixtures"
        />
        {showDropdown && <div className="navbar-search-menu">
            {searching && <p className="navbar-search-status">Searching…</p>}
            {!searching && !hasResults && <p className="navbar-search-status">No matches for "{term.trim()}".</p>}
            {teams.length > 0 && <section>
                <h4>Clubs</h4>
                {teams.map((teamResult) => <button type="button" key={teamResult.id} onClick={() => goTo(`/teams/${teamResult.id}`)}>
                    {teamResult.crest ? <img src={teamResult.crest} alt="" /> : <b>{teamResult.tla || teamResult.name.slice(0, 2)}</b>}
                    <span>{teamResult.name}</span>
                </button>)}
            </section>}
            {matches.length > 0 && <section>
                <h4>Matches</h4>
                {matches.map((matchResult) => <button type="button" key={matchResult.id} onClick={() => goTo(`/matches/${matchResult.id}`)}>
                    <span>{matchResult.home_team_name} <i>vs</i> {matchResult.away_team_name}</span>
                </button>)}
            </section>}
        </div>}
    </div>;
}

export default SearchBox;
