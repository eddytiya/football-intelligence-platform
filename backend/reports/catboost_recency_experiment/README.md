# CatBoost tuning and recency experiment

Twelve configurations completed using the saved model's 47,179 pre-match feature snapshots.
This experiment does not modify the production model or goal regressors.

## Method

- First approximately 60% trains candidates; next 20% selects settings and early-stopping iteration.
- Final approximately 20% compares only the selected candidate and fixed baseline.
- Boundaries move to the start of a match date so same-day fixtures remain together.
- Tuning: 2020-01-22 through 2023-04-06 (9,439 matches).
- Final evaluation: 2023-04-07 through 2026-05-24 (9,437 matches).
- Four parameter configurations crossed with all history, a trailing three-year training window, and exponential weighting with a two-year half-life.
- Recent-window strategies filter training rows only; historical feature calculations remain unchanged.
- Models train on results strictly before each evaluation period. Evaluation features incorporate earlier results as the period unfolds.

## Results

| Model | Final log loss (lower is better) | Final accuracy |
|---|---:|---:|
| Fixed baseline, all history | 0.987139 | 51.61598% |
| Tuned candidate, all history | 0.986694 | 51.60538% |

The selected candidate uses depth 4, learning rate 0.03, L2 regularisation 10 and 399 trees.
Log loss improves by approximately 0.000445; accuracy declines by one correct prediction.
Neither recent-history strategy beat the all-history winner on the tuning period.

Keep the current production model. These results do not demonstrate an accuracy improvement,
and the log-loss improvement is small. Confirm any proposed promotion across rolling chronological periods.

The evaluation overlaps the previously reported validation data and is not newly unseen data.
The baseline differs slightly from the prior saved metric because the original 80% split
divided a match date; this experiment keeps the whole date in evaluation, moving one match.

## Artifacts and reproduction

Run from `backend`:

```powershell
..\.venv\Scripts\python.exe scripts/experiment_catboost_recency.py
```

- `results.json`: boundaries, baseline, candidate and original saved metrics.
- `tuning_trials.json`: all twelve tuning results.
- `baseline_test_predictions.csv` and `tuning_winner_test_predictions.csv`: per-match final probabilities.
- `candidate.joblib`: experimental preprocessor and outcome classifier only; not a drop-in production artifact.
