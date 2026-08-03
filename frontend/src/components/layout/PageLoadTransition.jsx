import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import FootballLoader from "./FootballLoader";

function PageLoadTransition({ children }) {
    const location = useLocation();
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        setLoading(true);
        const timer = window.setTimeout(() => setLoading(false), document.readyState === "complete" ? 380 : 720);
        return () => window.clearTimeout(timer);
    }, [location.pathname, location.search]);
    return <>{loading && <FootballLoader fullScreen label="Loading the matchday" />}{children}</>;
}

export default PageLoadTransition;
