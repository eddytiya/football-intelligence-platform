import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { login, register } from "../api/authApi";
import "./Auth.css";

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
            setError(requestError.response?.data?.detail || "Unable to complete sign-in right now.");
        } finally {
            setLoading(false);
        }
    };

    return <main className="auth-page">
        <section className="auth-panel">
            <Link className="auth-brand" to="/"><b>FI</b><span>Football Intelligence Platform<small>Predict · Analyse · Win</small></span></Link>
            <span className="auth-kicker">Your matchday account</span>
            <h1>{isLogin ? "Welcome back." : "Build your matchday."}</h1>
            <p>{isLogin ? "Sign in to follow fixtures, forecasts and football intelligence from one private matchday hub." : "Create an account to begin saving your personalised football experience."}</p>
            <form onSubmit={submit}>
                <label>Email<input type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></label>
                <label>Password<input type="password" required minLength="8" autoComplete={isLogin ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></label>
                {error && <p className="auth-error">{error}</p>}
                {success && <p className="auth-success">{success}</p>}
                <button disabled={loading} type="submit">{loading ? "Please wait…" : isLogin ? "Enter matchday hub" : "Create account"}</button>
            </form>
            <footer>{isLogin ? <>New here? <Link to="/register">Create an account</Link></> : <>Already have an account? <Link to="/login">Sign in</Link></>}</footer>
        </section>
        <aside className="auth-visual">
            <div className="auth-visual-orbit"><i className="auth-ball" aria-hidden="true">⚽</i><span>Matchday access</span><strong>Every fixture.<br />One home.</strong><p>Follow clubs, explore forecasts, and keep the football world at your fingertips.</p><ul><li>Live fixtures and results</li><li>Model-based match forecasts</li><li>Club and league intelligence</li></ul></div>
        </aside>
    </main>;
}

export default Auth;
