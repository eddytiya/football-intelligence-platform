# Free-data form-feature experiment

## Outcome

Rolling-selection winner: **baseline**. The active website model was not changed.

None of the added feature groups beat the baseline on pooled overall accuracy or log loss. Retain the existing website model.

## Rolling website ensemble results

Each season is predicted using estimators fitted only on earlier dates. These results pool the non-overlapping 2023, 2024 and 2025 seasons.

| Feature variant | Matches | Accuracy | Log loss | PL prior-top-six accuracy |
|---|---:|---:|---:|---:|
| baseline | 8,748 | 51.93% | 0.986172 | 58.59% (594 matches) |
| opponent_adjusted | 8,748 | 51.71% | 0.986318 | 58.25% (594 matches) |
| recent_strength | 8,748 | 51.81% | 0.986485 | 58.75% (594 matches) |
| match_balance | 8,748 | 51.65% | 0.986503 | 58.42% (594 matches) |
| all_three | 8,748 | 51.84% | 0.986559 | 58.42% (594 matches) |

## Results by season

| Season | Feature variant | Website accuracy | Website log loss | Classifier accuracy | Classifier log loss |
|---|---|---:|---:|---:|---:|
| 2023 | baseline | 53.19% | 0.974693 | 52.81% | 0.974074 |
| 2023 | opponent_adjusted | 52.88% | 0.975705 | 52.91% | 0.976202 |
| 2023 | recent_strength | 52.88% | 0.974814 | 52.95% | 0.974453 |
| 2023 | match_balance | 52.85% | 0.975120 | 52.91% | 0.974893 |
| 2023 | all_three | 52.95% | 0.975177 | 52.78% | 0.974984 |
| 2024 | baseline | 52.16% | 0.986743 | 52.09% | 0.987373 |
| 2024 | opponent_adjusted | 52.19% | 0.986055 | 52.43% | 0.986065 |
| 2024 | recent_strength | 52.30% | 0.986630 | 52.23% | 0.987367 |
| 2024 | match_balance | 52.09% | 0.986706 | 52.16% | 0.987307 |
| 2024 | all_three | 52.26% | 0.986258 | 52.37% | 0.986505 |
| 2025 | baseline | 50.45% | 0.997079 | 50.55% | 0.997258 |
| 2025 | opponent_adjusted | 50.07% | 0.997195 | 50.27% | 0.997632 |
| 2025 | recent_strength | 50.24% | 0.998012 | 50.41% | 0.999408 |
| 2025 | match_balance | 50.00% | 0.997684 | 50.07% | 0.998336 |
| 2025 | all_three | 50.31% | 0.998242 | 50.31% | 0.999880 |

## Partial 2026 season comparison

Dates: 2026-08-07 to 2026-10-14. Only baseline and the variant selected on the earlier rolling periods are evaluated here.

| Feature variant | Matches | Website accuracy | Website log loss |
|---|---:|---:|---:|
| baseline | 559 | 50.09% | 0.986818 |

## Interpretation and limits

The current website's recorded 51.84% used a different chronological split. The matched comparisons above should not be presented as a direct change to that rate.

The 2026 slice is small and was already included in previous production-model training; it is held out only from this experiment. These are historical checks, not a fresh prospective test.

All candidate classifiers use the same fixed CatBoost settings. Goal regressors and Elo signals are identical between variants within each fold, isolating the additions to outcome classification. New features have not been tested in the goal regressors or retuned independently.

Top-six membership uses the previous season's reconstructed on-pitch standings, without disciplinary deductions. It does not use the evaluated season's final standings.

Paired calendar-week bootstrap intervals describe variability; they do not adjust for selecting among five variants.

Because the baseline won selection, the stored selected-minus-baseline bootstrap differences are zero by construction; they are not uncertainty estimates for the rejected feature groups.
All five website variants selected zero draws across the rolling periods; these additions did not resolve draw identification.

## Feature definitions

- Opponent-adjusted form: last-five/ten result residuals against pre-match Elo expectations, opponent rating averages, and the adjusted form gap. Home advantage is included before the past match result is observed.
- Recent strength: last-five/ten goals scored/conceded, differences from current-season rates, clean sheets, failed-to-score frequency and available history count. Rolling history survives season boundaries; momentum deltas are zero when the season denominator is empty.
- Match balance: absolute strength/form gaps, combined recent goal rates, and each team's historical draw frequency.

Every feature is calculated before updating state with that match's result. Dates remain together across training/evaluation boundaries.

## Cost and existing free data

This experiment uses the existing local archive only. No paid datasets, subscription upgrades, new accounts or external API requests are required by the experiment scripts.

The archive is from [Football-Data's downloadable CSV archive](https://football-data.co.uk/). Optional statistics already present locally are inventoried below; they were not added to these three feature groups.

| League | Matches | Shots on target available | HxG/AxG columns available |
|---|---:|---:|---:|
| BL1 | 4,941 | 4,940 | 45 |
| DED | 4,894 | 2,752 | 72 |
| ELC | 8,951 | 8,950 | 119 |
| FL1 | 5,811 | 5,810 | 54 |
| PD | 6,158 | 6,158 | 78 |
| PL | 6,140 | 6,140 | 60 |
| PPL | 4,703 | 2,825 | 71 |
| SA | 6,140 | 6,139 | 60 |

Shots and shots-on-target history offer another experiment without buying data, especially in the Premier League. Coverage varies by league. HxG/AxG coverage is limited to the partial 2026 season, so those columns alone cannot support the same long-history comparison.

## Validation and reproduction

39 unit tests passed, including five new checks for opponent weighting, cold-start handling, retained rolling history, draw frequency and exclusion of the current match's result. The regenerated baseline features exactly matched the active artifact's saved features and labels. The active model file's SHA-256 remained unchanged.

From the repository root:

```powershell
.\.venv\Scripts\python.exe backend/scripts/experiment_form_features.py
.\.venv\Scripts\python.exe backend/scripts/inspect_free_feature_data.py
.\.venv\Scripts\python.exe backend/scripts/report_form_features.py
```

Structured results, individual-fold results, final prediction CSVs and coverage inventories accompany this report. Experimental feature/model caches stay local and are excluded from Git.
