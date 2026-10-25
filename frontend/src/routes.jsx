import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";

import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Matches from "./pages/Matches";
import Predictions from "./pages/Predictions";
import AdminPredictions from "./pages/AdminPredictions";
import PredictionTracker from "./pages/PredictionTracker";
import ClubComparison from "./pages/ClubComparison";
import YourMatchday from "./pages/YourMatchday";
import FanVsModel from "./pages/FanVsModel";
import ConfidenceExplorer from "./pages/ConfidenceExplorer";
import ForecastMovement from "./pages/ForecastMovement";
import Competitions from "./pages/Competitions";
import CompetitionDetail from "./pages/CompetitionDetail";
import Teams from "./pages/Teams";
import TeamDetail from "./pages/TeamDetail";
import Analytics from "./pages/Analytics";
import Following from "./pages/Following";
import News from "./pages/News";
import Players from "./pages/Players";
import MatchCentre from "./pages/MatchCentre";
import Account from "./pages/Account";
import NotFound from "./pages/NotFound";
import Auth from "./pages/Auth";
import PageLoadTransition from "./components/layout/PageLoadTransition";

function hasSession() {
    try { return Boolean(JSON.parse(localStorage.getItem("football-auth") || "null")?.access_token); } catch { return false; }
}

function ProtectedRoute({ children }) {
    return hasSession() ? children : <Navigate to="/" replace />;
}

function AppRoutes() {
    return (
        <BrowserRouter>
            <PageLoadTransition><Routes>

                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Auth mode="login" />} />
                <Route path="/register" element={<Auth mode="register" />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/account" element={<ProtectedRoute><Account /></ProtectedRoute>} />
                <Route path="/admin/predictions" element={<ProtectedRoute><AdminPredictions /></ProtectedRoute>} />
                <Route path="/following" element={<ProtectedRoute><Following /></ProtectedRoute>} />
                <Route path="/prediction-tracker" element={<ProtectedRoute><PredictionTracker /></ProtectedRoute>} />
                <Route path="/compare" element={<ProtectedRoute><ClubComparison /></ProtectedRoute>} />
                <Route path="/your-matchday" element={<ProtectedRoute><YourMatchday /></ProtectedRoute>} />
                <Route path="/fan-vs-model" element={<ProtectedRoute><FanVsModel /></ProtectedRoute>} />
                <Route path="/confidence-explorer" element={<ProtectedRoute><ConfidenceExplorer /></ProtectedRoute>} />
                <Route path="/forecast-movement" element={<ProtectedRoute><ForecastMovement /></ProtectedRoute>} />
                <Route path="/news" element={<ProtectedRoute><News /></ProtectedRoute>} />
                <Route path="/players" element={<ProtectedRoute><Players /></ProtectedRoute>} />

                <Route
                    path="/matches"
                    element={<ProtectedRoute><Matches /></ProtectedRoute>}
                />
                <Route path="/matches/:matchId" element={<ProtectedRoute><MatchCentre /></ProtectedRoute>} />

                <Route
                    path="/predictions"
                    element={<ProtectedRoute><Predictions /></ProtectedRoute>}
                />

                <Route
                    path="/competitions"
                    element={<ProtectedRoute><Competitions /></ProtectedRoute>}
                />

                <Route path="/competitions/:competitionId" element={<ProtectedRoute><CompetitionDetail /></ProtectedRoute>} />

                <Route
                    path="/teams"
                    element={<ProtectedRoute><Teams /></ProtectedRoute>}
                />

                <Route path="/teams/:teamId" element={<ProtectedRoute><TeamDetail /></ProtectedRoute>} />


                <Route
                    path="/analytics"
                    element={<ProtectedRoute><Analytics /></ProtectedRoute>}
                />


                <Route path="*" element={<NotFound />} />

            </Routes></PageLoadTransition>
        </BrowserRouter>
    );
}

export default AppRoutes;
