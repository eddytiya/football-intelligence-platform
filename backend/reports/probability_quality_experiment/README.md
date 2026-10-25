# Blending and calibration experiment

Completed D + E with three existing outcome-model types and nine probability recipes.
The production artifact and website model were not changed.

## Chronological design

| Block | Dates | Matches | Purpose |
|---|---|---:|---|
| Training | 2010-08-06 to 2020-01-21 | 28,303 | Fit the three base models |
| Calibration | 2020-01-22 to 2021-10-01 | 4,721 | Fit blend weights and temperatures |
| Selection | 2021-10-02 to 2023-04-05 | 4,718 | Choose the probability recipe |
| Final evaluation | 2023-04-07 to 2026-05-24 | 9,437 | Compare selected recipe with matched CatBoost baseline |

Dates remain together across boundaries. All base models stay frozen after training,
so calibration is fitted to predictions on later matches, not training predictions.
Feature snapshots contain prior results as the evaluation periods unfold.

The base models use the existing fixed CatBoost, LightGBM and calibrated logistic-regression settings.
Blends search 66 nonnegative weight combinations summing to one, in increments of 0.1.
Calibration uses a positive temperature on log probabilities, bounded between 0.25 and 4.
Recipes cover the three individual models, their temperature-calibrated versions,
an uncalibrated blend, a calibrated blend, and a blend of calibrated models.
Only calibration labels fit weights/temperatures; selection labels choose the recipe.
Final labels are used only for reporting the baseline and selected candidate.

## Results

| Model | Final log loss (lower is better) | Final accuracy |
|---|---:|---:|
| CatBoost, matched training period | 0.988255 | 51.65837% |
| Selected calibrated blend | 0.987713 | 51.81731% |

Selected recipe: 90% CatBoost, 10% calibrated logistic regression, 0% LightGBM,
followed by temperature scaling with T = 1.102408. This slightly softens confidence.
Positive temperature scaling preserves the winning class; the accuracy change comes from blending.
The candidate improves log loss by 0.000542 and accuracy by 0.15895 percentage points (15 matches).

## Interpretation

This is a small improvement over the matched CatBoost baseline. It does not establish
a consistent improvement across seasons or statistical significance.
The earlier A + C tuned candidate scored 0.986694 log loss, better than this candidate,
but used 37,742 training matches versus 28,303 here. Do not attribute the difference solely to the method.
The final evaluation period overlaps previously inspected validation data; it is not a fresh holdout.
Confirm with rolling chronological evaluation before promoting a recipe.
Only temperature scaling was tested; other calibration methods were not evaluated.

## Reproduce and inspect

Run from `backend`:

```powershell
..\.venv\Scripts\python.exe scripts/experiment_probability_quality.py
..\.venv\Scripts\python.exe scripts/test_probability_quality.py
```

Four numerical tests passed: identity/argmax preservation, correction of synthetic
overconfidence, recovery of a known best blend, and rejection of invalid distributions.
Every experiment probability array is checked for finite, nonnegative values summing to one.
Class ordering is checked as away win, draw, home win.

- `results.json`: period boundaries, all nine selection results, recipe and final metrics.
- `catboost_test_predictions.csv`: matched baseline probabilities.
- `blend_calibrated_test_predictions.csv`: selected candidate probabilities.
- `candidate.joblib`: frozen base models and selected recipe; experimental bundle, not a production replacement.
