import { Link } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import "./NotFound.css";

function NotFound() {
    return <MainLayout><section className="not-found-page">
        <span>Offside</span>
        <h1>This fixture is not on the board.</h1>
        <p>The page may have moved, or the link may not exist. Return to the hub and choose your next match.</p>
        <div><Link to="/">Open dashboard</Link><Link to="/matches">Browse matches</Link></div>
    </section></MainLayout>;
}

export default NotFound;
