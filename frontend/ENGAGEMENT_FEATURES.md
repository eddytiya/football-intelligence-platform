# Personal matchday and forecast evidence

## Routes

- `/your-matchday`: account-followed club shortcuts and watchlisted fixtures, deduplicated by fixture ID. Upcoming/live/results views, club filtering, local saved-forecast previews, calendar export and links to forecast/game. Club lists contribute their available upcoming fixtures and up to five recent results. Partial endpoint failure is explicit; refresh retries. Legacy Following remains available in Explore.
- `/fan-vs-model?match=<id>`: one final home/draw/away pick per account/fixture. The server authenticates the account, checks status/kickoff, attempts an existing local-model forecast, then rechecks under a fixture row lock before storing. Changed identities/kickoff during inference reject the request. Duplicate submissions return 409. Picks cannot be edited through the API. Model probabilities/version are frozen, never regenerated at settlement.
- `/confidence-explorer`: ten probability bands for top-pick confidence or a selected outcome; mean probability, observed frequency, counts, plot and sample-weighted ECE. It uses one earliest valid browser-saved forecast per eligible completed fixture. League/model filters and sample caveats prevent presenting this as a whole-model evaluation.
- `/forecast-movement?match=<id>`: browser-local observations made when a verified pre-match forecast is viewed. Shows first/latest changes in percentage points, a timestamp-scaled three-series plot, exact values/retrieval times/model versions and an explicit version-change warning. It does not reconstruct missing history, monitor continuously, infer causes or change the model.

## Persistence and scoring

`FanPick` is the additive `fan_picks` table, created idempotently at backend startup. Its unique account/fixture constraint prevents multiple picks. The API returns only the current account's records. Settled scoring requires a past-kickoff FINISHED fixture, valid scores, unchanged clubs and a submission before both captured and current kickoff. Excluded statuses and unavailable model snapshots never enter paired accuracy. Fan-all, fan-paired and model-paired counts are labelled separately. Exact model ties use home/draw/away order. No prizes or stakes are involved.

The existing browser tracker archive remains unchanged by movement capture. `football-forecast-observations` records actual visits, deduplicates identical observations within one minute, and retains at most 200 per fixture/5,000 overall. Clearing site data removes it. It is not account-synced or tamper-proof. Cached forecasts retain their earlier retrieval time. Legacy original snapshots appear as such, not invented earlier observations.

Club profile/directory upcoming queries now exclude elapsed scheduled fixtures and include TIMED fixtures before applying limits. Other model behaviour, training, prediction APIs and saved history remain intact. No paid dependency or new raster asset was added.

## Verification

Production build succeeds; lint exits with eight incumbent hook dependency warnings and Vite retains its large-chunk advisory. Ten Node tests verify scoring/calendar/observation deduplication/original-snapshot preservation/calibration boundaries/paired denominators. Seven in-memory SQLite backend tests cover authentication, account privacy, duplicates, inference crossing kickoff, changed fixtures, absent models, settlement and future club fixtures. The existing alias regression also passes.

Desktop/mobile browser checks exercise personal-feed views, radio submission/locked reload, outcome calibration bins and movement tables/charts. Real forecast capture confirms one first-visit observation with the original archive timestamp. Evidence: `.impeccable/review/engagement/`; filled probability examples and browser game responses are explicitly controlled QA fixtures in isolated profiles, not production performance. No real account favourites or game picks were changed by these browser fixtures. Independent UI review disposition: ship, with no material fixes.
