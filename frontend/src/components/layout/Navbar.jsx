import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "./Navbar.css";
import Logo from "./Logo";
import SearchBox from "./SearchBox";
import NotificationBell from "./NotificationBell";
import AccountMenu from "./AccountMenu";
import NavMenu from "./NavMenu";
import ThemeToggle from "./ThemeToggle";
import apiClient from "../../api/apiClient";

function Navbar() {
    const navigate = useNavigate();
    const [account, setAccount] = useState(() => {
        try { return JSON.parse(localStorage.getItem("football-auth") || "null")?.user || null; } catch { return null; }
    });

    useEffect(() => {
        let active = true;
        if (localStorage.getItem("football-auth")) {
            apiClient.get("/auth/me").then(({ data: user }) => {
                if (!active) return;
                const session = JSON.parse(localStorage.getItem("football-auth") || "null");
                if (session) {
                    localStorage.setItem("football-auth", JSON.stringify({ ...session, user }));
                    setAccount(user);
                }
            }).catch(() => {});
        }
        const refresh = () => {
            try { setAccount(JSON.parse(localStorage.getItem("football-auth") || "null")?.user || null); } catch { setAccount(null); }
        };
        window.addEventListener("football-auth-updated", refresh);
        return () => { active = false; window.removeEventListener("football-auth-updated", refresh); };
    }, []);

    const logout = () => { localStorage.removeItem("football-auth"); window.dispatchEvent(new Event("football-auth-updated")); navigate("/"); };

    return (
        <nav className="custom-navbar">
            <div className="navbar-container">

                <NavLink to={account ? "/dashboard" : "/"} className="logo">
                    <Logo />
                    <div className="brand-text">
                        <h3>Football Intelligence Platform</h3>
                        <p>Your matchday, understood.</p>
                    </div>
                </NavLink>

                <NavMenu account={account} />

                <div className="nav-actions">
                    <ThemeToggle />
                    <SearchBox />
                    {account && <NotificationBell />}
                    {account ? <AccountMenu account={account} onLogout={logout} /> : <NavLink className="navbar-login" to="/login">Sign in</NavLink>}
                </div>

            </div>
        </nav>
    );
}

export default Navbar;
