import Navbar from "./Navbar";
import Footer from "./Footer";
import { useLocation } from "react-router-dom";

function MainLayout({ children }) {
    const { pathname } = useLocation();
    const isDashboard = pathname === "/dashboard";

    return (
        <div className={isDashboard ? "app-shell dashboard-shell" : "app-shell football-shell"}>
            <a className="flood-skip" href="#main-content">Skip to content</a>
            <Navbar />

            <main id="main-content">
                {children}
            </main>

            <Footer />
        </div>
    );
}

export default MainLayout;
