# Prediction data repairs — 17 October 2026

The local application now uses the verified season-aware artifact. The preceding production
artifact is retained as `original_model_before_repairs.joblib` for recovery.

## Completed fixes

- **Team identity:** Removed fuzzy substitution from the prediction path. Deliberate aliases,
  exact archive identities and a unique canonical match are accepted. Current-season league
  membership is checked separately. All 457 historically supported database league/team
  combinations resolve to an exact identity after refreshing the source archive. Unknown
  and unsupported clubs receive an unavailable response rather than another club's statistics.
- **Season features:** Points, appearances, goals and home/away season rates reset at each
  season boundary; table positions include only that season's members. Elo, recent form and
  head-to-head retain their separate histories. All 47,738 saved snapshots have valid table
  positions within their league-season team count, versus 16,673 invalid snapshots in the old audit.
- **Fresh states:** Downloaded 559 validated current-season completed results across eight leagues.
  Premier League history now ends 12 October 2026; Championship history ends 14 October.
  Accepted history refreshes daily while the backend runs; caches notice source/artifact changes
  and rebuild feature states without refitting estimators on each request. Refresh failures retain
  the last accepted file; forecasts pause once league history is older than 45 days.
- **Invalid results:** Eight records are currently quarantined: six future-finished results
  and two malformed statuses. Counts differ from the original audit because another future
  result appeared during the live sync window. All original dates and scores are preserved,
  with before-change JSON backups and `restore_quarantine.py` for recovery. Earlier overbroad
  cleanup passes were fully restored; 22,886 legacy records lacking both date fields were
  preserved for separate provenance review. No historical rows were deleted.
- **Ingestion guards:** Provider validation and ORM write hooks reject future finished results,
  malformed statuses and missing/invalid final scores. Existing undated legacy updates are
  preserved; new finished records require a date. Accepted database statuses are not used as
  a substitute for provider CSV training truth.
- **Website evaluation:** Backtested the actual 50% outcome ML / 25% Elo / 25% goal-model
  Poisson forecast using pre-match snapshots and models fitted only before the date cutoff.
  Validation metrics are available through `/predictions/model/status`. Response metadata
  identifies the model version and history cutoff. Current states cannot be used to predict
  already-played historical fixtures. The legacy prediction service uses fixture kickoff for features.
- **Browser history:** New saved forecasts retain model version and probability vectors and
  preserve the first saved pre-kickoff prediction instead of overwriting it on re-request.
  History remains browser-local and limited to 30 records; it is not a server-side live evaluation ledger.

## Measured results

| Forecast | Historical accuracy | Log loss |
|---|---:|---:|
| Repaired CatBoost classifier | 51.82% | 0.9866 |
| Exact website ensemble | 51.84% | 0.9860 |

Validation uses 9,551 matches from 12 May 2023 through the latest accepted results.
The serving estimators are refitted on all accepted data after evaluation; these metrics
belong to the held-out evaluation run, not an evaluation of the refit on its training data.
Candidate selection uses the same validation period, so it is not a pristine final holdout.
Earlier experiments also inspected much of this period. Updated source coverage changes
the cutoff and row count, so this is not a controlled before/after comparison against the old 51.77%.
The repairs do not demonstrate 60% overall accuracy.

## Draw experiment: evaluated, not forced

Using repaired features, tested draw class weights 1.0, 1.25, 1.5 and 2.0.
Models and goal regressors train on the first 60%; the next 20% selects the weight by log loss;
the final 20% compares the selected model against the unweighted baseline. Dates remain together.

| Draw weight | Selection accuracy | Selection log loss | Correct draws / predicted draws |
|---|---:|---:|---:|
| 1.0 | 51.31% | 0.99502 | 0 / 0 |
| 1.25 | 51.17% | 0.99692 | 6 / 28 |
| 1.5 | 50.93% | 1.00032 | 135 / 497 |
| 2.0 | 48.41% | 1.00960 | 744 / 2,598 |

Increasing draw frequency hurt both requested metrics on selection data, so it was rejected.
Draw identification remains a modelling weakness: the website ensemble selected no draws
in its main held-out evaluation, although it assigns nonzero draw probabilities.
Further improvement requires informative draw-related features or a validated alternative;
there is no evidence that forcing draws fixes overall accuracy.

## Validation and recovery

- 34 unit tests pass, covering aliases, unknown-club rejection, season resets, chronology,
  stale-state guards, membership, probability/class alignment, provider validation,
  failed-refresh preservation, ORM write guards, endpoint error handling, rescheduled
  kickoff correction, and rejection of provider-ID/team mismatches.
- Frontend production build passes.
- Full-artifact verification: 47,738 finite feature snapshots, zero invalid positions,
  zero unresolved supported identities, zero future-finished database records, and
  successful upcoming-fixture forecasts (`verification.json`).
- The original classifier artifact is backed up locally; quarantine snapshots are excluded
  from Git and must be retained locally for recovery. Do not restore quarantined results
  without confirming provider provenance.

## Reproduce

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe backend/scripts/refresh_prediction_history.py
.\.venv\Scripts\python.exe backend/scripts/validate_prediction_repairs.py
```

Training: `HistoricalMatchModel().train(artifact_path)` builds schema-v2 features, compares
three outcome classifiers, evaluates goal regressors and the website ensemble, then saves
the refitted artifact atomically. Refreshing accepted CSVs updates serving states; model
retraining remains an explicit offline task.

Detailed outputs: `history_refresh.json`, `training_metrics.json`, `verification.json`,
`draw_weighting.json`, `verified_mappings.csv`, and `../website_ensemble_validation.csv`.
