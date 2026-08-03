import React from "react";
import ReactDOM from "react-dom/client";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import "./index.css";

import App from "./App.jsx";
import AppErrorBoundary from "./components/layout/AppErrorBoundary.jsx";
// Load the route-scoped football visual system after page styles so it can
// intentionally refine the existing components without touching Dashboard.
import "./styles/football-theme.css";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <AppErrorBoundary><App /></AppErrorBoundary>
    </React.StrictMode>
);
