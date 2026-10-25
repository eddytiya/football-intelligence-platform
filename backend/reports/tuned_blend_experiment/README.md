# Tuned CatBoost plus calibrated blending

Completed four inner CatBoost tuning trials followed by nine probability recipes.
The live website and production model artifact are unchanged.

## Method

Same chronological blocks as the preceding probability-quality experiment:

| Block | Matches | Purpose |
|---|---:|---|
| Training, through 2020-01-21 | 28,303 | Tune and fit base models |
| Calibration, 2020-01-22 to 2021-10-01 | 4,721 | Fit blend weights and calibration |
| Selection, 2021-10-02 to 2023-04-05 | 4,718 | Choose recipe by log loss |
| Final evaluation, 2023-04-07 to 2026-05-24 | 9,437 | Report matched baseline and selected recipe |

CatBoost tuning uses an inner chronological split inside the first training block:
21,210 matches train; 7,093 matches from 2017-09-30 onward select settings with early stopping.
This avoids choosing tree count using the later blend/calibration or recipe-selection labels.
The chosen settings are depth 4, learning rate 0.03, L2 regularisation 10, and 347 trees.
The earlier experiment's 399-tree model is not reused because its tree count was selected
on periods now reserved for calibration and recipe selection.

Refit the selected settings on all 28,303 training rows, then freeze base models.
Blend logistic regression, LightGBM and tuned CatBoost using nonnegative weights
in increments of 0.1. Fit temperature scaling on calibration rows only.
Use the selection period to choose among nine recipes. Final labels never fit parameters.
Same-day fixtures remain together at boundaries; features incorporate only prior results.

## Final results

| Candidate | Log loss (lower is better) | Accuracy |
|---|---:|---:|
| Tuned CatBoost alone, matched training data | 0.987870 | 51.81731% |
| Tuned CatBoost plus calibrated blend | 0.987368 | 51.78553% |

The selected blend is 90% tuned CatBoost, 10% calibrated logistic regression,
and 0% LightGBM, followed by temperature scaling with T = 1.102571.
Compared with matched tuned CatBoost, log loss improves by 0.000502,
while accuracy falls by 0.03178 percentage points (three correct predictions).
Temperature scaling preserves the winning class; accuracy changes come from blending.

For context, the preceding untuned calibrated blend scored 0.987713 and 51.81731%
on the same final rows and training block. The new blend improves its log loss by 0.000345
but loses three correct predictions. Neither comparison demonstrates gains in both metrics.

The earlier A + C model scored 0.986694 log loss and 51.60538% accuracy using 37,742
training matches. It has better log loss but used more training data, so it is not a matched baseline.

## Limits and validation

The final evaluation reuses previously inspected validation data and is not a fresh holdout.
Changes are small and statistical significance has not been established.
Confirm across rolling chronological periods before changing the website model.
Four probability numerical tests passed. Runtime checks validate probability distributions,
class ordering, and disjoint chronological blocks. Production artifacts were not modified.

## Reproduce

From `backend`:

```powershell
..\.venv\Scripts\python.exe scripts/experiment_probability_quality.py --tuned-catboost
..\.venv\Scripts\python.exe scripts/test_probability_quality.py
```

`results.json` contains inner tuning, all recipe-selection metrics and final results.
`catboost_test_predictions.csv` and `blend_calibrated_test_predictions.csv` contain
the matched final probabilities. `candidate.joblib` is an experimental frozen-model
bundle and recipe, not a drop-in production artifact.
