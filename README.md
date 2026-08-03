# Football Intelligence Platform

A full-stack football fixture, club intelligence, analytics and prediction platform. It combines stored historical results with scheduled/live fixture data to present transparent match forecasts rather than betting advice or guarantees.

## What the platform currently does

- **Dashboard**: next fixtures, recent forecast-versus-result records and a personalised saved-club feed.
- **Matches**: date navigation, scheduled/completed/live filtering, matchweeks, team search, favourites and auto-refreshing score data.
- **Predictions**: match result probabilities, expected goals, likely scorelines, confidence, goal markets, form, model reasoning, head-to-head context, saved forecast history and season forecasts.
- **Competitions**: club directory, fixtures by matchweek, standings, team-strength/race insights, historical top scorers and a five-season predicted final table.
- **Teams**: all stored clubs, club profiles, favourite clubs, squad data where synced, honours, form, fixtures, historical results and side-by-side club/head-to-head comparison.
- **Analytics**: league and team performance, head-to-head explorer, form/strength insights, historical top-scorer import and season outlooks.

## Architecture

```text
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
```

## Local development

1. Create `backend/.env` from `backend/.env.example`; never commit real API keys.
2. Start PostgreSQL and create the database named in the environment file.
3. From `backend`, apply migrations and start the API:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

   Or just run `.\dev.ps1` from `backend/` — it launches the same command. Always keep `--reload`
   on for local work; without it, edits you save keep running against the old code until you
   manually kill and restart the process.

4. From `frontend`, install and run the UI:

```powershell
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000`. For another deployment, set `VITE_API_BASE_URL` in the hosting environment.

## Data and model notes

- Historical match data powers form, team attack/defence, ELO-style strength, scoreline and season-table estimates.
- A forecast is **not a guarantee**. Football is inherently uncertain; confidence describes the available separation/coverage, not certainty.
- Live results update through a conservative free-tier-safe polling interval. New schedules are imported separately and only appear once a provider publishes them.
- Player/squad and historic scorer coverage depends on API-Football availability and the free request quota. It is intentionally selective to keep the project free-tier friendly.

## Hosting checklist

- Keep `.env` files and API keys out of GitHub.
- Host the frontend as a static Vite build and set `VITE_API_BASE_URL` to the deployed backend URL.
- Configure the backend CORS origin for the deployed frontend URL.
- Use managed PostgreSQL for production; do not upload local database dumps or large raw historical datasets unless the host/storage plan supports them.
- Run Alembic migrations during deployment, then start the FastAPI service.

## Best next additions

1. Authenticated user accounts and cloud-synced favourite clubs/alerts.
2. Scheduled background jobs via a hosted cron service, so live data updates continue when the web server sleeps.
3. Reliable player injuries, lineups, assists and advanced player statistics from a paid/approved source.
4. Automated model retraining and a model-version page showing training date, input coverage and validation methodology.
5. Notifications for saved-club kick-offs, results and prediction-ready fixtures.
6. A CI workflow that runs frontend builds, backend tests and migration checks for every pull request.
