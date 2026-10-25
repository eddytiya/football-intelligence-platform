import "./FootballLoader.css";
import { TbBallFootball } from "react-icons/tb";

function FootballLoader({ label = "Preparing your football hub", fullScreen = false }) {
    return <div className={`football-loader ${fullScreen ? "football-loader-fullscreen" : ""}`} role="status" aria-live="polite">
        <div className="football-loader-ball" aria-hidden="true"><TbBallFootball /></div>
        <strong>{label}</strong>
        <span>Loading football data</span>
    </div>;
}

export default FootballLoader;
