import Navbar from "./Navbar";
import Footer from "./Footer";
import { useLocation } from "react-router-dom";

function MainLayout({ children }) {
    const { pathname } = useLocation();
    const isDashboard = pathname === "/dashboard";

    return (
        <div className={isDashboard ? "app-shell dashboard-shell" : "app-shell football-shell"}>
            <Navbar />

            <main>
                {children}
            </main>

            <Footer />
        </div>
    );
}

export default MainLayout;
