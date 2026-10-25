# Past-shot features: free local data experiment

## Outcome

Selected by rolling website log loss: **shots_combined**. The active website artifact was not changed.

The selected forecast scores 52.19% accuracy and 0.983149 log loss across 8,748 rolling-validation matches. The matched baseline scores 51.93% and 0.986172.

Accuracy increases by 0.263 percentage points (23 additional correct predictions). The paired accuracy interval crosses zero, so the accuracy gain remains uncertain; the log-loss improvement is clearer. Retain the candidate for further testing rather than claiming 60% or changing the active model from these results alone.

## Rolling comparisons

Three expanding training windows evaluate the full 2023, 2024 and 2025 seasons. Classifiers, preprocessing and goal models fit only earlier dates. The exact website mix is 50% classifier, 25% Elo and 25% goal-model Poisson probabilities.

| Features | Matches | Website accuracy | Website log loss | PL accuracy | PL prior-top-six accuracy |
|---|---:|---:|---:|---:|---:|
| baseline | 8,748 | 51.93% | 0.986172 | 53.07% (1140) | 58.59% (594) |
| shots | 8,748 | 51.94% | 0.983335 | 53.51% (1140) | 59.60% (594) |
| shots_on_target | 8,748 | 51.99% | 0.984354 | 53.25% (1140) | 59.26% (594) |
| shots_combined | 8,748 | 52.19% | 0.983149 | 53.25% (1140) | 59.60% (594) |

## Individual seasons

| Season | Features | Website accuracy | Website log loss | Classifier accuracy | Classifier log loss |
|---|---|---:|---:|---:|---:|
| 2023 | baseline | 53.19% | 0.974693 | 52.81% | 0.974074 |
| 2023 | shots | 53.02% | 0.971510 | 53.09% | 0.969844 |
| 2023 | shots_on_target | 53.29% | 0.973057 | 53.29% | 0.971765 |
| 2023 | shots_combined | 53.36% | 0.971986 | 53.29% | 0.970764 |
| 2024 | baseline | 52.16% | 0.986743 | 52.09% | 0.987373 |
| 2024 | shots | 52.33% | 0.982763 | 52.47% | 0.981774 |
| 2024 | shots_on_target | 52.30% | 0.983737 | 52.57% | 0.982270 |
| 2024 | shots_combined | 52.40% | 0.982486 | 52.50% | 0.980946 |
| 2025 | baseline | 50.45% | 0.997079 | 50.55% | 0.997258 |
| 2025 | shots | 50.48% | 0.995732 | 50.38% | 0.997013 |
| 2025 | shots_on_target | 50.38% | 0.996269 | 50.79% | 0.996781 |
| 2025 | shots_combined | 50.82% | 0.994976 | 50.82% | 0.995107 |

## Partial 2026 check

Dates: 2026-08-07 to 2026-10-14. Only the baseline and the earlier rolling-selection winner are checked here.

| Features | Matches | Website accuracy | Website log loss |
|---|---:|---:|---:|
| baseline | 559 | 50.09% | 0.986818 |
| shots_combined | 559 | 50.98% | 0.983984 |

Partial-season paired 95% intervals: log-loss difference [-0.006958927865614288, 0.0007224391627584596]; accuracy difference [-0.004945990398293029, 0.02679009103641456]. Both include zero in this run, so the small 2026 sample does not establish a reliable gain by itself.

## Paired uncertainty

Calendar weeks are resampled together to retain within-week dependence. These descriptive 95% bootstrap intervals are not adjusted for selection among variants. Differences are candidate minus baseline: negative log-loss differences and positive accuracy differences favour the candidate.

| Features | Log-loss difference interval | Accuracy difference interval |
|---|---|---|
| shots | [-0.003949055306961602, -0.001817732884466811] | [-0.003914086182418172, 0.0040156262088540335] |
| shots_on_target | [-0.0027263222529341565, -0.0009263444929745909] | [-0.0027865007302834486, 0.0035904426498269476] |
| shots_combined | [-0.004096134124965564, -0.0019571932577798633] | [-0.0012624544889529856, 0.00653412330580379] |

## Data and feature definitions

Read 47,738 fixtures from existing local CSVs. Complete valid home/away shot pairs: 43,712; complete shots-on-target pairs: 43,712. Invalid-statistic incidents masked: 2. No fixture is dropped because its statistics are missing.

- **Shots:** last-five/ten fixture averages for shots for/against, shot differences and observed-match counts.
- **Shots on target:** the equivalent last-five/ten target-shot averages, differences and observation counts.
- **Combined:** both groups plus last-ten shot accuracy for/against, defined as total on-target shots divided by total shots on rows with both measurements.

Windows count actual fixtures, including those with missing measurements. Missing statistics stay NaN and receive explicit coverage counts; median imputation learns only from the training period. Observed zero shots stay zero. Negative/fractional counts and targets exceeding total shots are treated as invalid, not silently used as valid evidence.

Statistics are appended to team history only after that day's feature snapshots have been generated. Current-match shots, current-match goals and future results cannot enter their own pre-match inputs. Rolling histories remain within each competition and may span season changes or long breaks.

The classifier receives the additional features. Goal regressors and Elo remain identical between variants within each fold, so this is a controlled classifier-feature test rather than a complete redesign of the website ensemble.

## Cost and limits

Existing local data only: no subscriptions, purchases, external requests, new accounts or extra datasets are needed for this experiment.

The 2026 slice is small and already appeared in earlier production training; it is held out only from this experiment. Earlier historical validation periods have also been inspected. These are not prospective live accuracy measurements, and they must not replace the website's separately recorded 51.84% as though evaluated on the same split.

Premier League top-six labels use the previous season's on-pitch table, excluding disciplinary deductions. Shot coverage varies by league and season. No betting odds or current-match expected-goals columns are used.

## Validation and reproduction

The shot-feature unit tests cover home/away reversal, missing-versus-zero handling, expiry by actual-fixture windows, current-match exclusion and invalid-statistic masking. Rebuilt baseline features and labels exactly match the active artifact. The active artifact SHA-256 is checked before and after the experiment.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe backend/scripts/experiment_shot_features.py
.\.venv\Scripts\python.exe backend/scripts/report_shot_features.py
```

Structured results, individual-season comparisons, per-fixture rolling/final probabilities and a local experimental bundle accompany this report. The bundle and feature cache are excluded from Git and do not replace the website model.
