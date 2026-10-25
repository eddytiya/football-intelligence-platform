# Prediction data audit — 17 October 2026

Read-only audit of 128 source CSVs, 47,179 saved pre-match snapshots, 9,437 historical
baseline predictions, the prediction code paths, and the connected PostgreSQL database.
No model retraining, production artifact replacement, database edits or website changes were performed.

## Main findings and recommended order

### 1. Correct team identities before trusting website forecasts

Of 633 distinct database league/team combinations, 70 in historically supported leagues
resolve below the existing 0.8 name-confidence threshold. All 70 have a scheduled/timed
fixture in the 30-day window starting on the audit date. This is name-match confidence,
not an estimate of prediction correctness. Many matches are correct identities with low
string similarity; others are wrong identities.

Examples from the current resolver:

| Provider name, Premier League | Resolved historical name | Confidence | Assessment |
|---|---|---:|---|
| Manchester City FC | mancity | 0.609 | Correct identity but low string confidence |
| Manchester United FC | manunited | 0.667 | Correct identity but low string confidence |
| Leeds United FC | sheffieldunited | 0.571 | Wrong identity |
| Coventry City FC | mancity | 0.476 | Wrong identity; Coventry absent from PL archive |

The historical endpoint still calculates probabilities for low-confidence mappings and
returns `review_required`; the MatchCard consumer does not explicitly check that field.
Fix provider-ID-to-canonical-team mappings, including competition membership, and withhold
unresolved forecasts. Do not solve this by lowering the confidence threshold.

Evidence: `database_team_mappings.csv`; `_resolve_team` and `predict_fixtures` in
`backend/app/services/machine_learning/historical_match_model.py`; MatchCard's `showPrediction`.

### 2. Repair season context in features

16,673 of 47,179 snapshots (35.34%) contain at least one league position greater than the
number of teams in that league-season. `_league_position` ranks every historical team in a
league using cumulative points; its table includes clubs that left that competition.
Team state is reset once at dataset construction, not at each new season.

Example: Liverpool's opening 2025-season snapshot has `home_games = 570`, reflecting
archive history rather than current-season appearances. Long-term statistics may be useful,
but they need separate names and features from genuine current-season table positions and rates.
Season boundaries and current membership need explicit handling; Elo can retain a separate
cross-season prior.

Evidence: `positions_outside_season_team_count.csv`, `season_opening_features.csv`, `feature_statistics.csv`.

### 3. Refresh states, and validate database results before using them

The artifact was trained on 2 August 2026, but source results end in May 2026:
Premier League results stop on 24 May, 146 days before the audit date.
Training date is not data freshness. The website loads saved states once per process;
the audited inference path does not incorporate newly finished database matches into those states.

The database contains newer results, but also **five fixtures dated 18 October 2026 already
marked FINISHED with scores**, after this audit date. It also contains two status strings that
are timestamps rather than match statuses. These records need provenance review before
they can be used as training truth. The audit does not establish their cause.

Database status FINISHED rows have no missing scores, but that does not validate their truth.
Five saved LGBMClassifier predictions have timestamps at or after kickoff; those must not
be treated as pre-match validation observations. Timestamp-before-kickoff alone also does
not prove all other saved predictions are leakage-free or use the website's model.

Evidence: `results.json`, `database_future_finished.csv`, `database_finished_missing_scores.csv`.

### 4. Measure the exact forecast shown on the website

Our experimental accuracy values measure an outcome classifier. The website endpoint
returns an ensemble: **50% classifier + 25% Elo + 25% Poisson from goal regressors**.
These are different forecasts. The classifier experiments do not establish website accuracy.

There is also a separate legacy PredictionService loading `trained_models/best_model.joblib`,
distinct from the historical artifact used by MatchCard. Its saved metadata names logistic regression.
Metrics and saved predictions need explicit model versions and prediction-path identity.

Loaded historical-model states contain final archive results, not historical states as of a requested date.
A sampled completed PL fixture produced 25 changed inputs when evaluated with final states instead
of its original pre-match snapshot. Passing a historical match date alone does not rewind states.
The older PredictionService additionally builds features using current time rather than fixture kickoff.
Backtesting must reconstruct features and model training at each cutoff; do not backtest the current
loaded artifact against matches it already includes.

The browser's saved history keeps only 30 forecasts, overwrites a match's entry on re-request,
and does not persist probability vectors or model versions. Those browser-local records were
not accessible to this audit. Save immutable pre-kickoff probabilities server-side for live evaluation.

### 5. Investigate draw errors with a separate experiment

The fixed CatBoost baseline predicted draws just 26 times in 9,437 matches.
There were 2,398 actual draws, of which only two were selected correctly: draw recall **0.083%**.
This is a clear limitation for identifying draws, but it does not prove class reweighting
will improve overall accuracy or log loss. A draw can receive a reasonable probability
without being the most likely individual outcome. Test draw-related features and decision
rules on earlier periods, with both accuracy and log loss reported.

Confusion matrix, rows actual and columns predicted, order away win / draw / home win:

| Actual | Away win | Draw | Home win |
|---|---:|---:|---:|
| Away win | 1,574 | 9 | 1,329 |
| Draw | 806 | 2 | 1,590 |
| Home win | 817 | 15 | 3,295 |

## Historical performance breakdown

These numbers describe the fixed CatBoost baseline on 7 April 2023–24 May 2026,
using the earlier experiment's grouped-by-date 80% training cutoff. They are not new
out-of-sample results and do not evaluate the website ensemble or the latest tuned blend.

| Segment | Matches | Accuracy | Log loss |
|---|---:|---:|---:|
| All eight leagues | 9,437 | 51.62% | 0.98714 |
| Premier League | 1,234 | 53.24% | 0.98795 |
| PL, involving previous season's top six | 644 | 57.76% | 0.93363 |
| PL, other matches | 590 | 48.31% | 1.04724 |
| Netherlands | 982 | 55.09% | 0.94839 |
| Portugal | 990 | 54.55% | 0.92044 |
| Spain | 1,250 | 53.36% | 0.97308 |
| Germany | 990 | 51.92% | 0.98280 |
| Italy | 1,240 | 51.45% | 0.98907 |
| France | 1,008 | 50.69% | 1.00288 |
| English Championship | 1,743 | 46.07% | 1.04836 |

Previous-season top six use reconstructed on-pitch points, goal difference and goals,
without disciplinary point deductions. No current-season final positions are used to label this segment.

The model beats an always-home baseline of 43.73% on these rows. Matches involving
newly promoted/new-to-league teams score 52.58%, versus 51.18% for other matches;
this breakdown does not support assuming promoted clubs are the main error source.

Season-start-year accuracy declines from 52.13% in 2023 to 51.92% in 2024 and 50.17%
in 2025; the 2022 slice is partial. Changing football conditions or cumulative features
could contribute, but this audit does not establish causality.

Confidence bands also separate easier from harder matches (`errors_by_confidence.csv`),
but subset performance does not satisfy the user's target of 60% across all matches.

## Checks that passed

- Source archive: 47,194 rows, 47,179 usable matches, 15 discarded rows with missing date/teams/scores.
- No duplicate fixture rows by league/date/home/away in the usable source archive.
- No negative or fractional scorelines, same-team matches, or recorded-result/score disagreements.
- All 47,179 saved snapshot identities and outcome labels match the source archive.
- No missing or nonfinite numeric snapshot features.
- Final prediction dates, row counts and outcome labels match the expected saved snapshot order.
- Database queries ran inside a read-only transaction; no updates were issued.

These checks do not independently verify provider result accuracy or full season completeness.
The prediction CSVs lack fixture IDs, so alignment also relies on the known deterministic saved order.

## Next experiment

First fix canonical team identity, validate suspect database records, and separate season-aware
table/form features from long-term strength. Then rerun the same chronological comparison
and backtest the website ensemble itself. Keep the production model until those changes are
validated. The audit identifies repair opportunities; it does not establish that they will reach 60%.

## Reproduce

From the repository root:

```powershell
.\.venv\Scripts\python.exe backend/scripts/audit_prediction_data.py
```

Full structured findings: `results.json`. Detailed CSVs accompany this report.
