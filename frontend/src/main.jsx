import React from "react";
import ReactDOM from "react-dom/client";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import "./index.css";

import App from "./App.jsx";
import AppErrorBoundary from "./components/layout/AppErrorBoundary.jsx";
// Preserve the feature layouts, then apply one visual system across all routes.
import "./styles/feature-layout.css";
import "./styles/football-theme.css";
import "./styles/fonts.css";
import "./styles/stadium-appearance.css";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <AppErrorBoundary><App /></AppErrorBoundary>
    </React.StrictMode>
);
