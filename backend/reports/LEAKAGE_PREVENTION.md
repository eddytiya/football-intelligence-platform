# Prediction chronology and evidence

Protocol version: 1. Feature/artifact schema: 3.

## Live forecasts

- CSVs provide calendar dates, so the entire current UTC day is excluded from training and rolling history. Every feature/result date must be strictly earlier than the prediction reference day and fixture day.
- All public generation paths, including the older batch/single endpoints, use the audited historical model. The old database-feature model is not used for API generation.
- Every response records model version, `training_data_through`, `history_through`, and `leakage_protocol_version`. Unverified artifacts fail closed.
- The server saves the first pre-kickoff forecast per match/model without rewriting it. Live accuracy uses the first eligible server forecast per match, checked against both original and current kickoff. Only completed matches with final scores enter the denominator.
- Old forecasts without the required metadata remain stored but are excluded. Legacy predictions/evaluations are explicitly unverified and cannot enter trusted accuracy or create new legacy evaluations.

## Training and evaluation

- Features use strictly earlier calendar days. Season membership is accumulated chronologically instead of looking across the entire future season.
- Distinct match days are divided into 60% initial training, 20% selection, 20% final test. Model choice uses only the selection block. Test labels are not used to choose the winner.
- Calibration uses forward, day-aligned folds. Imputation, scaling and encoding live inside each fold's estimator, so they never fit the later calibration fold.
- The selected estimator and fixed goal models are fitted on the first 80% and scored on the final chronological block. Metrics are frozen before fitting the deployable model on all eligible history.
- `website_ensemble_validation.csv` now contains the final test block (the filename is retained for compatibility). Exact boundaries and metrics are in the model artifact and `/predictions/model/status`.

## Historical backtests

- Historical matches never use the fully trained current estimator. A separate model is fitted using only matches before the first day of the target month.
- The backtest specification is fixed in code: regularized logistic regression, Poisson goal regressors and the fixed 50/25/25 ensemble. It does not reuse a model selected using subsequent seasons.
- Preprocessing and team mapping fit only pre-cutoff history. Rolling form is reconstructed using only days earlier than the target day. The current target result and later results are never inputs.
- Backtests have their own immutable archive kind and model versions. Their page comparison is separate from actual recorded live accuracy. Current head-to-head and league-outlook panels are omitted from historical analyses because those feeds are not point-in-time reconstructions.

## Limits

Historical source files are today's accepted archive. The project has no historical provider publication/revision timestamps, so historical backtests demonstrate chronological out-of-sample modelling under the assumption that earlier-day results were available. They do not prove the exact data originally available at each historic kickoff. Going forward, server timestamps and immutable snapshots provide prospective evidence. Retuning after repeatedly inspecting the final test would require a new untouched period.

Verification includes future-result/team-name perturbations leaving earlier fitted weights and model version unchanged; day boundaries; fold-local preprocessing; missing/same-day cutoff rejection; archived live timing; API review of matches 993, 998 and 1012; and separation of live and historical metrics. The latest API audit is saved in `leakage_prevention_verification.json`.
