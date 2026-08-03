import "./FootballLoader.css";

function FootballLoader({ label = "Preparing your football hub", fullScreen = false }) {
    return <div className={`football-loader ${fullScreen ? "football-loader-fullscreen" : ""}`} role="status" aria-live="polite">
        <div className="football-loader-ball" aria-hidden="true">⚽</div>
        <strong>{label}</strong>
        <span>Loading live football intelligence</span>
    </div>;
}

export default FootballLoader;
