import { useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import "./AccountMenu.css";

function AccountMenu({ account, onLogout }) {
    const containerRef = useRef(null);
    const [open, setOpen] = useState(false);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) setOpen(false);
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const name = account.email.split("@")[0];
    const initial = name.slice(0, 1).toUpperCase();

    return <div className="account-menu" ref={containerRef}>
        <button type="button" className="account-menu-trigger" onClick={() => setOpen((value) => !value)} aria-label="Account menu">
            <span className="account-menu-avatar">{initial}</span>
            <span className="account-menu-name">{name}</span>
            <b className={`account-menu-chevron ${open ? "is-open" : ""}`}>⌄</b>
        </button>
        {open && <div className="account-menu-dropdown">
            <NavLink to="/following" onClick={() => setOpen(false)}>Following</NavLink>
            <NavLink to="/account" onClick={() => setOpen(false)}>Account</NavLink>
            <button type="button" onClick={() => { setOpen(false); onLogout(); }}>Sign out</button>
        </div>}
    </div>;
}

export default AccountMenu;
