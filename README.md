⚽ Football Intelligence Platform
A full-stack football fixture, club intelligence, analytics and prediction platform. It combines stored historical results with scheduled/live fixture data to present transparent match forecasts — not betting advice or guarantees.

<p align="left"> <img alt="React" src="https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB?logo=react&logoColor=black"> <img alt="FastAPI" src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white"> <img alt="PostgreSQL" src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white"> <img alt="ML" src="https://img.shields.io/badge/ML-CatBoost%20%2B%20LightGBM-orange"> </p>
Screenshots
Save each screenshot into docs/screenshots/ with the filename shown, then commit — GitHub renders them inline automatically. Delete any row you don't have a screenshot for.

Page	Screenshot
Landing page	Landing
Sign up / log in	Auth
Dashboard	Dashboard
Matches (fixture list)	Matches
Match Centre (single match detail)	Match Centre
Predictions	Predictions
Competitions (club directory)	Competitions
Competition detail (table / matchweeks)	Competition Detail
Teams	Teams
Team detail / club profile	Team Detail
Players	Players
Analytics	Analytics
News	News
Following (saved clubs feed)	Following
Account	Account
What the platform currently does
Dashboard — next fixtures, recent forecast-versus-result records and a personalised saved-club feed.
Matches — date navigation, scheduled/completed/live filtering, matchweeks, team search, favourites and auto-refreshing score data, plus a per-match Match Centre view.
Predictions — match result probabilities, expected goals, likely scorelines, confidence, goal markets, form, model reasoning, head-to-head context, saved forecast history and season forecasts.
Competitions — club directory, fixtures by matchweek, standings, team-strength/race insights, historical top scorers and a five-season predicted final table.
Teams — all stored clubs, club profiles, favourite clubs, squad data where synced, honours, form, fixtures, historical results and side-by-side club/head-to-head comparison.
Players — synced squad and player data where available from the opted-in API-Football source.
Analytics — league and team performance, head-to-head explorer, form/strength insights, historical top-scorer import and season outlooks.
News — football news feed, sorted by recency.
Following / Account — saved-club following feed and user account management.
Architecture
React + Vite frontend (5173)
        |
        | HTTP / JSON
        v
FastAPI backend (8000)
        |
        +-- PostgreSQL: fixtures, teams, historical results, standings, predictions
        +-- football-data.org: fixtures, live scores and competition data
        +-- API-Football: opted-in squad/player data on the free quota
        +-- historical datasets: model training and head-to-head history
        |
        v
CatBoost / LightGBM prediction models (backend/app/ml + ml-engine)
Tech stack
Layer	Tools
Frontend	React 19, Vite, React Router, Recharts, Bootstrap, Axios
Backend	FastAPI, SQLAlchemy, Alembic, PostgreSQL
ML / Prediction	CatBoost, LightGBM, scikit-learn
Data sources	football-data.org, API-Football, historical match datasets
Deployment	Neon (DB), Render (backend), Vercel (frontend) — see DEPLOY.md
Local development
Create backend/.env from backend/.env.example. Never commit real API keys.

Start PostgreSQL and create the database named in the environment file.

From backend, apply migrations and start the API:

..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Or just run .\dev.ps1 from backend/ — it launches the same command. Always keep --reload on for local work; without it, edits you save keep running against the old code until you manually kill and restart the process.

From frontend, install and run the UI:

npm install
npm run dev
The frontend defaults to http://localhost:8000. For another deployment, set VITE_API_BASE_URL in the hosting environment.

Project structure
football-intelligence-platform/
├── frontend/        React + Vite single-page app (pages, components, hooks, API client)
├── backend/         FastAPI service — routes, models, schemas, ETL, ML inference, Alembic migrations, tests
├── ml-engine/        offline feature engineering, model training and prediction pipeline
├── docs/            project documentation and screenshots
├── scripts/         utility and data scripts
├── render.yaml       Render deployment config
└── DEPLOY.md         step-by-step free-tier deployment guide (Neon + Render + Vercel)
Data and model notes
Historical match data powers form, team attack/defence, ELO-style strength, scoreline and season-table estimates.
A forecast is not a guarantee. Football is inherently uncertain; confidence describes the available separation/coverage, not certainty.
Live results update through a conservative free-tier-safe polling interval. New schedules are imported separately and only appear once a provider publishes them.
Player/squad and historic scorer coverage depends on API-Football availability and the free request quota. It is intentionally selective to keep the project free-tier friendly.
Prediction models (CatBoost / LightGBM) are trained offline in ml-engine/ and served from backend/app/ml/saved_models/.
Deployment
See DEPLOY.md for the full free-tier walkthrough (Neon Postgres + Render backend + Vercel frontend). Quick checklist:

Keep .env files and API keys out of GitHub.
Host the frontend as a static Vite build and set VITE_API_BASE_URL to the deployed backend URL.
Configure the backend CORS origin for the deployed frontend URL.
Use managed PostgreSQL for production; do not upload local database dumps or large raw historical datasets unless the host/storage plan supports them.
Run Alembic migrations during deployment, then start the FastAPI service.
Best next additions
Authenticated user accounts and cloud-synced favourite clubs/alerts.
Scheduled background jobs via a hosted cron service, so live data updates continue when the web server sleeps.
Reliable player injuries, lineups, assists and advanced player statistics from a paid/approved source.
Automated model retraining and a model-version page showing training date, input coverage and validation methodology.
Notifications for saved-club kick-offs, results and prediction-ready fixtures.
A CI workflow that runs frontend builds, backend tests and migration checks for every pull request.
