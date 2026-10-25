# Football Intelligence Platform

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Football fans following clubs and match forecasts. The user confirmed that the primary tasks are finding a match and understanding its forecast, alongside following favourite clubs, fixtures and results.

## Product Purpose

Bring match discovery, understandable forecasts and club following into one football website. Help fans see what is happening, understand the probabilities for an upcoming match and return to the clubs and fixtures they follow.

## Operating Context

The existing web app uses React and Vite with a Python/FastAPI backend. Local development uses the frontend at http://127.0.0.1:5173 and the backend at http://127.0.0.1:8000 when running. Start the frontend with `npm run dev` from `frontend/`.

The current implementation has a public landing page and registration/sign-in. Signed-in routes cover the dashboard, matches and match centre, predictions, competitions, teams, following, news, players, analytics and account settings. These routes describe existing functionality, not an agreement that every route deserves equal prominence.

## Capabilities and Constraints

- Preserve finding fixtures, viewing results, understanding forecasts and following favourite clubs as core workflows.
- Existing personal features include favourites and a fixture watchlist; preserve saved user data and authentication during visual redesign.
- The user requires free data and services and does not want paid subscriptions or data purchases.
- Forecasts cover home win, draw and away win probabilities, with expected-goal estimates and model reasoning where available. Make probability and uncertainty understandable to football fans.
- Accuracy and log loss are distinct evaluation measures. Lower log loss is better. Never present model confidence as measured accuracy, or an experimental result as live website performance.
- Previously discussed 55% and 60% overall accuracy figures are goals, not achieved product claims. Do not invent performance, freshness, live coverage or success claims.
- Historical experiments and the active website model can use different validation periods. Any performance display needs its actual source, sample and period.
- Future visual work should preserve product behaviour and factual content. This initialization records product context; it does not select a replacement visual identity.

## Brand Commitments

The existing product name is Football Intelligence Platform. The user explicitly requires a football-centred identity with clearly visible, real club crests and an ambitious level of visual finish. The user rejected the first sparse, letter-badge previews as too basic. They selected Under the floodlights: dark stadium surfaces, large club crests, bold match headings and lime accents. Their supplied broadcast reference adds prominent monochrome crests, team-name plates and a central fixture-information column to the featured matchup. Preserve crest detail; do not flatten coloured logos into unreadable white silhouettes.

## Evidence on Hand

- Frontend routes and implemented pages: `frontend/src/routes.jsx` and `frontend/src/pages/`.
- Current forecast and fixture presentation: `frontend/src/components/` and frontend API integrations.
- Historical experiment results and their limitations: `backend/reports/shot_context_experiment/README.md` and `results.json`.
- Earlier model comparisons: `backend/reports/tuned_shot_stack_experiment/`.
- Data repair documentation: `backend/reports/data_repairs/README.md`.
- Existing historical football data and the active local model are available in the backend. Their existence alone does not establish current fixture coverage or prospective accuracy.

## Product Principles

1. Let fans find a match and understand its forecast quickly.
2. Make favourite clubs, fixtures and results easy to return to.
3. Show probabilities and performance honestly, with their limitations.
4. Work within free-data and free-service constraints.
5. Preserve working football and account functionality through the redesign.

## Open Decisions

The first redesign covers the dashboard and match forecast experience, with desktop and mobile given equal priority. Full forecast breakdowns open on the match's own page. Longer-term deployment and any product-specific accessibility requirements remain undecided. The code-first workflow preference is stored separately in `.impeccable/config.json`.
