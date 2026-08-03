import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import { getAccountFavourites } from "../../api/accountApi";
import { getTeamProfile } from "../../api/teamApi";
import "./NavMenu.css";

const NAV_ITEMS = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/matches", label: "Matches" },
    { to: "/predictions", label: "Predictions" },
    { to: "/competitions", label: "Competitions" },
    { to: "/teams", label: "Teams" },
    { to: "/players", label: "Players" },
    { to: "/news", label: "News", hasSubmenu: true },
    { to: "/analytics", label: "Analytics" },
];

function NavMenu({ account }) {
    const zoneRef = useRef(null);
    const closeTimer = useRef(null);
    const [open, setOpen] = useState(false);
    const [newsOpen, setNewsOpen] = useState(false);
    const [followedClubs, setFollowedClubs] = useState([]);

    useEffect(() => {
        if (!account) { setFollowedClubs([]); return; }
        getAccountFavourites().then((rows) => {
            const teamIds = rows.filter((row) => row.entity_type === "team").map((row) => row.entity_id).slice(0, 5);
            return Promise.all(teamIds.map((id) => getTeamProfile(id).catch(() => null)));
        }).then((profiles) => setFollowedClubs(profiles.filter(Boolean))).catch(() => setFollowedClubs([]));
    }, [account]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (zoneRef.current && !zoneRef.current.contains(event.target)) {
                setOpen(false);
                setNewsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const openNow = () => {
        window.clearTimeout(closeTimer.current);
        setOpen(true);
    };
    const closeSoon = () => {
        closeTimer.current = window.setTimeout(() => { setOpen(false); setNewsOpen(false); }, 200);
    };

    return <div
        className={`nav-hover-zone ${open ? "is-open" : ""}`}
        ref={zoneRef}
        onMouseEnter={openNow}
        onMouseLeave={closeSoon}
        onClick={() => setOpen((value) => !value)}
    >
        {!open && <span className="nav-hover-hint" aria-hidden="true">•••</span>}
        {open && <div className="nav-hover-links">
            {NAV_ITEMS.map((item) => item.hasSubmenu ? (
                <div className="nav-hover-item-with-sub" key={item.to} onMouseEnter={() => setNewsOpen(true)} onMouseLeave={() => setNewsOpen(false)}>
                    <NavLink to={item.to} onClick={() => setOpen(false)}>{item.label}</NavLink>
                    {newsOpen && <div className="nav-hover-submenu">
                        <NavLink to="/news" onClick={() => setOpen(false)}>Football news</NavLink>
                        {followedClubs.map((club) => <NavLink key={club.id} to={`/news?club=${encodeURIComponent(club.name)}`} onClick={() => setOpen(false)}>{club.name} news</NavLink>)}
                    </div>}
                </div>
            ) : <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)}>{item.label}</NavLink>)}
        </div>}
    </div>;
}

export default NavMenu;
