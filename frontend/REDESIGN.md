# Under the floodlights

The approved matchday identity now spans the public landing/auth pages and signed-in football pages. The shared visual source is `src/styles/football-theme.css`, supported by self-hosted Barlow Condensed and DM Sans fonts (`public/fonts`, with OFL notices). `feature-layout.css` retains the incumbent feature layouts without retaining the old colour theme.

The dashboard uses stored fixtures, followed clubs, real three-way forecasts and a stored-results league table. Fixture search/view/competition filters work locally within the displayed feed; the full fixture browser remains available. Detailed context, player coverage, saved forecast results and season estimates remain accessible under More football intelligence.

Fixtures open a dedicated match page with the shared stadium-backed matchup. Probabilities lead; existing form, expected-goal, comparison, coverage and reasoning panels remain available below. Watchlists persist to the existing account API. Upcoming forecasts use the existing historical prediction API. The earliest saved browser snapshot is retained, including after a model update or result. Past/unverified fixtures do not receive newly generated pre-match forecasts. No backend model or training code changed for this redesign.

Large matchup crests use explicit reviewed vector mappings in `src/utils/clubCrests.js` through `ClubCrest variant="broadcast"`. Eight clubs have monochrome assets: Real Madrid, Manchester United, Barcelona, Arsenal, Manchester City, Newcastle United, Bayern Munich and Juventus. Other clubs retain their original colour crest until a suitable vector is added. Colour crests stay in compact lists and standings. Source credits and adaptation notes: `public/crests/monochrome/README.md`.

The decorative stadium is sourced from Unsplash; its origin is embedded in `public/images/stadium.jpg` and recorded in the neighbouring JSON. It is generic decoration, never a representation of the fixture’s venue.

Twelve competition emblems are stored locally to avoid depending on third-party image latency. Their original provider URLs are recorded in `public/images/competitions/sources.json`. The remaining competition uses its provider image with the shared initials fallback on failure.

## Verification

- Frontend production build succeeds. The current single JavaScript chunk exceeds Vite’s 500 kB advisory threshold; no runtime/build error results.
- Lint completes with eight existing React hook dependency warnings in legacy pages/components, without new errors.
- Browser checks cover the public and authenticated routes at 1440 px desktop and 390 px mobile widths. Evidence and observations: `.impeccable/review/` in the project root.
- Interaction checks cover mobile menu/Escape/focus, fixture filtering and empty states, original forecast retention across reload, watchlist persistence (test-account changes restored), dedicated match navigation and actual SVG loading.
- Independent finish review confirmed all eight scored fixes resolved after desktop/mobile recaptures; final disposition is recorded in `.impeccable/review/final-verdict.md`.
- Tests use the local preview account and isolated browser profiles. No user messages, paid resources, subscriptions or external publishing are involved.

Remaining scope: the whole club catalogue does not yet have monochrome vectors. Free data coverage and endpoint latency still govern which forecasts, events, lineups and analytics can be shown. Missing data stays explicit rather than being replaced with sample values.
