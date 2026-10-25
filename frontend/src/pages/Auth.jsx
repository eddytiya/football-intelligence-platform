import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { login, register } from "../api/authApi";
import "./Auth.css";
import Logo from "../components/layout/Logo";
import ClubCrest from "../components/ClubCrest";
import ThemeToggle from "../components/layout/ThemeToggle";

function Auth({ mode }) {
    const isLogin = mode === "login";
    const navigate = useNavigate();
    const location = useLocation();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(location.state?.message || "");

    const submit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");
        try {
            const payload = await (isLogin ? login(email, password) : register(email, password));
            if (isLogin) {
                localStorage.setItem("football-auth", JSON.stringify(payload));
                window.dispatchEvent(new Event("football-auth-updated"));
                navigate("/dashboard");
            } else {
                navigate("/login", { replace: true, state: { message: "Account created. Sign in with your email and password." } });
            }
        } catch (requestError) {
            setError(requestError.response?.data?.detail || (isLogin ? "Unable to sign in right now. Please try again shortly." : "Unable to create your account right now. Please try again shortly."));
        } finally {
            setLoading(false);
        }
    };

    return <main className="auth-page">
        <section className="auth-panel">
            <div className="auth-appearance"><ThemeToggle /></div>
            <Link className="auth-brand" to="/"><Logo /><span>Football Intelligence Platform<small>Your matchday, understood.</small></span></Link>
            <h1>{isLogin ? "Welcome back." : "Build your matchday."}</h1>
            <p>{isLogin ? "Sign in to follow fixtures, forecasts and football intelligence from one private matchday hub." : "Create an account to begin saving your personalised football experience."}</p>
            <form onSubmit={submit}>
                <label>Email<input type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></label>
                <label>Password<input type="password" required minLength={isLogin ? 1 : 8} autoComplete={isLogin ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={isLogin ? "Your password" : "At least 8 characters"} /></label>
                {error && <p className="auth-error">{error}</p>}
                {success && <p className="auth-success">{success}</p>}
                <button disabled={loading} type="submit">{loading ? "Please wait…" : isLogin ? "Enter matchday hub" : "Create account"}</button>
            </form>
            <footer>{isLogin ? <>New here? <Link to="/register">Create an account</Link></> : <>Already have an account? <Link to="/login">Sign in</Link></>}</footer>
        </section>
        <aside className="auth-visual">
            <a className="stadium-day-credit" href="/images/stadiums/credits.html#arsenal" target="_blank" rel="noopener noreferrer">Daylight photo credit</a>
            <div className="auth-visual-orbit"><div className="flood-auth-crests">{["Real Madrid", "Manchester United", "FC Barcelona"].map((name) => <ClubCrest key={name} name={name} variant="broadcast" alt={`${name} crest`} />)}</div><strong>Your club.<br />Your matchday.</strong><p>Follow the football that matters to you. Understand what the numbers can—and can’t—tell you.</p></div>
        </aside>
    </main>;
}

export default Auth;
