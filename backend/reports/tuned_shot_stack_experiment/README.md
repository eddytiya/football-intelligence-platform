# Tuned shot classifier and shot-feature goal regressors

## Outcome

Selected by pooled rolling website log loss: **shots_with_shot_goals**. The active website artifact was not changed.

Compared with the previous shot candidate, rolling accuracy is 52.19% versus 52.19%; log loss is 0.982617 versus 0.983149. The best rolling result uses fixed classifier settings and shot features in both goal regressors. Tuning did not beat that stack in this grid.

The partial 2026 check is mixed: shot-based goal models improve overall accuracy over the previous shot candidate but worsen log loss. Premier League top-six rolling accuracy also declines slightly. This does not establish a general accuracy upgrade or justify claiming 60%; retain the candidate for further validation and keep the active website model unchanged.

Controls reproduce the preceding shot experiment's exact rolling match identities, outcome labels and probabilities to absolute tolerance 1e-12.

## Rolling comparisons

Evaluate the full 2023, 2024 and 2025 seasons using expanding training windows. Settings and tree counts are selected on the prior completed season inside each training window. No outer validation-season labels fit or tune its estimators.

| Forecast | Matches | Accuracy | Log loss | Home goal MAE | Away goal MAE | PL prior-top-six accuracy |
|---|---:|---:|---:|---:|---:|---:|
| current_baseline | 8,748 | 51.93% | 0.986172 | 0.9169 | 0.8253 | 58.59% (594) |
| shots_fixed | 8,748 | 52.19% | 0.983149 | 0.9169 | 0.8253 | 59.60% (594) |
| shots_tuned | 8,748 | 52.01% | 0.983396 | 0.9169 | 0.8253 | 59.26% (594) |
| shots_with_shot_goals | 8,748 | 52.19% | 0.982617 | 0.9159 | 0.8261 | 59.26% (594) |
| shots_tuned_with_shot_goals | 8,748 | 52.10% | 0.982829 | 0.9159 | 0.8261 | 59.09% (594) |

Variant definitions:

- `current_baseline`: current fixed-settings classifier and goal regressors, all using baseline features.
- `shots_fixed`: previous 52.19% rolling candidate; fixed shot classifier with baseline goal models.
- `shots_tuned`: nested-tuned shot classifier with baseline goal models.
- `shots_with_shot_goals`: fixed shot classifier and shot features in both goal regressors.
- `shots_tuned_with_shot_goals`: tuned shot classifier and shot features in both goal regressors.

Goal MAE measures goal prediction error, not match-outcome accuracy. All variants use the exact website probability combination: 50% classifier, 25% Elo, 25% Poisson from the two goal regressors.

## By season

| Season | Forecast | Accuracy | Log loss | Home goal MAE | Away goal MAE |
|---|---|---:|---:|---:|---:|
| 2023 | current_baseline | 53.19% | 0.974693 | 0.9428 | 0.8483 |
| 2023 | shots_fixed | 53.36% | 0.971986 | 0.9428 | 0.8483 |
| 2023 | shots_tuned | 53.09% | 0.971875 | 0.9428 | 0.8483 |
| 2023 | shots_with_shot_goals | 53.09% | 0.971780 | 0.9435 | 0.8485 |
| 2023 | shots_tuned_with_shot_goals | 53.05% | 0.971618 | 0.9435 | 0.8485 |
| 2024 | current_baseline | 52.16% | 0.986743 | 0.8942 | 0.8241 |
| 2024 | shots_fixed | 52.40% | 0.982486 | 0.8942 | 0.8241 |
| 2024 | shots_tuned | 52.50% | 0.982603 | 0.8942 | 0.8241 |
| 2024 | shots_with_shot_goals | 52.43% | 0.981726 | 0.8922 | 0.8252 |
| 2024 | shots_tuned_with_shot_goals | 52.57% | 0.981842 | 0.8922 | 0.8252 |
| 2025 | current_baseline | 50.45% | 0.997079 | 0.9139 | 0.8036 |
| 2025 | shots_fixed | 50.82% | 0.994976 | 0.9139 | 0.8036 |
| 2025 | shots_tuned | 50.45% | 0.995711 | 0.9139 | 0.8036 |
| 2025 | shots_with_shot_goals | 51.06% | 0.994346 | 0.9120 | 0.8046 |
| 2025 | shots_tuned_with_shot_goals | 50.69% | 0.995026 | 0.9120 | 0.8046 |

## Selected tuning settings

Classifier log loss selects settings within the earlier inner season; pooled outer website log loss selects the final stack. The tuning grid includes depths 4/5/6, learning rates 0.03/0.05 and L2 values 5/10/20 in four predefined combinations. Early stopping chooses tree count, with patience 60 and a maximum of 250 or 700 trees depending on configuration.

| Outer test season | Inner tuning season | Trees | Depth | Learning rate | L2 |
|---|---|---:|---:|---:|---:|
| 2023 | 2022 | 405 | 4 | 0.03 | 10 |
| 2024 | 2023 | 510 | 6 | 0.03 | 10 |
| 2025 | 2024 | 471 | 4 | 0.03 | 10 |

## Partial 2026 check

Only the current baseline, previous fixed shot candidate and the stack selected on earlier periods are checked. The 559-row partial season was inspected previously and is not a fresh prospective holdout.

| Forecast | Matches | Accuracy | Log loss | Home goal MAE | Away goal MAE |
|---|---:|---:|---:|---:|---:|
| current_baseline | 559 | 50.09% | 0.986818 | 0.9859 | 0.8820 |
| shots_fixed | 559 | 50.98% | 0.983984 | 0.9859 | 0.8820 |
| shots_with_shot_goals | 559 | 51.34% | 0.984904 | 0.9707 | 0.8856 |

## Paired uncertainty

Calendar-week bootstrap intervals are descriptive and not corrected for choosing among candidates. Differences are candidate minus reference: lower log loss and higher accuracy are favourable. Accuracy differences below are proportions, not percentage points.

| Forecast | Reference | Log-loss difference 95% interval | Accuracy difference 95% interval |
|---|---|---|---|
| shots_fixed | current_baseline | [-0.004096134124965567, -0.001957193257779864] | [-0.0012624544889529856, 0.00653412330580379] |
| shots_tuned | current_baseline | [-0.003924433512976723, -0.0017114559404635056] | [-0.0027853905812181877, 0.0043200585401288304] |
| shots_with_shot_goals | current_baseline | [-0.004960044861050454, -0.0021219590838740293] | [-0.0017113812980767739, 0.006617999880438131] |
| shots_tuned_with_shot_goals | current_baseline | [-0.004721211442875645, -0.0020222209945925246] | [-0.0024530742931077243, 0.0055494431456131425] |
| shots_tuned | shots_fixed | [-0.00019925724383343773, 0.0006414112362875445] | [-0.0038959832722695914, 0.00012043065787901369] |
| shots_with_shot_goals | shots_fixed | [-0.0010139222076247798, -8.167261365897307e-05] | [-0.00199578703770122, 0.0017661245392371079] |
| shots_tuned_with_shot_goals | shots_fixed | [-0.0009168472440112868, 0.00023685569667697686] | [-0.0031849563124775357, 0.0012202112885066102] |

## Cost, safety checks and limits

No paid services, downloads or additional datasets were used. Reused the local 47,738-row pre-match feature cache from the preceding experiment. Current-shot features remain excluded from the current prediction; missing statistics are handled by training-only imputation and explicit coverage counts.

47 unit tests passed, including chronological boundary checks, a mocked tuning test that proves the outer season is excluded, and website probability validation. The original model file's SHA-256 remained unchanged. The two control forecasts reproduced the previous experiment exactly.

Goal regressors retain their fixed MAE objective and existing hyperparameters; their controlled change is the addition of lagged shot features. A lower goal MAE does not necessarily imply lower outcome log loss.

Historical periods and the partial 2026 slice were used in earlier experiments. These results do not establish 60% live accuracy. Prior-season top-six labels reconstruct on-pitch results without disciplinary deductions. The current website's earlier 51.84% metric uses a different split; compare the matched controls in this report.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe backend/scripts/experiment_tuned_shot_stack.py
.\.venv\Scripts\python.exe backend/scripts/report_tuned_shot_stack.py
```

Prerequisite: `shot_feature_experiment/features.joblib` from the earlier shot-feature run. This report directory contains complete tuning trials, period metrics, per-match predictions and an experimental candidate bundle. The bundle is not a drop-in production artifact and remains excluded from Git.
